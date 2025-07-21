import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from pydantic import SecretStr
import requests

# === LangGraph imports ===
from langgraph.graph import StateGraph, START
from typing_extensions import TypedDict

load_dotenv()

# 1. Define the shared state for orchestration
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# 2. Step 1: retrieve relevant articles
def retrieve(state: State) -> Dict[str, Any]:
    # use your existing ClickHouse-based retriever
    # docs = state_app.clickhouse_dao.related_articles(state["question"], limit=state_app.max_articles)
    docs = requests.get(f"http://localhost:8000/related-articles?query={state['question']}").json()
    # convert to LangChain Documents
    documents = [
        Document(
            page_content=body,
            metadata={
                "url": url,
                "title": title,
                "publication_date": pub_date,
                "similarity_score": score
            }
        )
        for url, title, body, pub_date, score in docs
    ]
    return {"context": documents}

# 3. Step 2: generate answer with Claude
def generate(state: State) -> Dict[str, Any]:
    # build context string
    ctx = "\n\n".join(
        f"Title: {doc.metadata['title']}\n"
        f"Date: {doc.metadata['publication_date']}\n"
        f"Content: {doc.page_content}"
        for doc in state["context"]
    )
    prompt_str = state_app.rag_prompt.format(question=state["question"], context=ctx)
    response = state_app.llm.invoke(prompt_str)
    return {"answer": response.content}

class RAGApplication:
    def __init__(self, max_articles: int = 5):
        # — your existing initialization —
        self.max_articles = max_articles
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        self.llm = ChatAnthropic(
            model_name="claude-3-5-sonnet-latest",
            api_key=SecretStr(api_key),
            temperature=0.1,
            timeout=60,
            stop=[]
        )
        self.rag_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
            You are a helpful AI assistant that answers questions based on the provided context from Guardian articles.

            Context from Guardian articles:
            {context}

            Question: {question}

            Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to answer the question, say so. Use the Guardian articles as your primary source of information.

            Answer:"""
                    )

        # 4. Build the LangGraph orchestration
        builder = StateGraph(State).add_sequence([retrieve, generate])
        builder.add_edge(START, "retrieve")
        self.graph = builder.compile()

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Invoke the orchestrated RAG graph in one call."""
        try:
            # run through retrieve → generate
            result_state = self.graph.invoke({"question": question})
            # unpack
            answer = result_state["answer"]
            docs: List[Document] = result_state["context"]

            return {
                "question": question,
                "answer": answer,
                "articles_used": len(docs),
                "context": [
                    {
                        "title": d.metadata["title"],
                        "url": d.metadata["url"],
                        "publication_date": d.metadata["publication_date"],
                        "similarity_score": d.metadata["similarity_score"],
                        "snippet": (d.page_content[:200] + "...") if len(d.page_content) > 200 else d.page_content
                    }
                    for d in docs
                ]
            }
        except Exception as e:
            logging.error(f"RAG pipeline failed: {e}")
            return {
                "question": question,
                "answer": f"Error: {e}",
                "context": [],
                "articles_used": 0
            }

# === Example usage ===
if __name__ == "__main__":
    state_app = RAGApplication(max_articles=5)
    for q in [
        "Give me the latest on news corp columnist Lucy Zelić.",
    ]:
        res = state_app.answer_question(q)
        print(f"\nQuestion: {res['question']}")
        print(f"Answer: {res['answer']}")
        print(f"Articles used: {res['articles_used']}")
        print("-" * 60)
