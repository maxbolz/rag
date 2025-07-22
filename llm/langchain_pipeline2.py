import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Union
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
    docs = requests.get(f"http://localhost:8000/related-articles?query={state['question']}").json()
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
def generate(state: State, app: "Pipeline2Application") -> Dict[str, Any]:
    ctx = "\n\n".join(
        f"Title: {doc.metadata['title']}\n"
        f"Date: {doc.metadata['publication_date']}\n"
        f"Content: {doc.page_content}"
        for doc in state.get("context", [])
    )
    prompt_str = app.rag_prompt.format(question=state["question"], context=ctx)
    response = app.llm.invoke(prompt_str)
    return {"answer": response.content}

class Pipeline2Application:
    def __init__(self, mode_or_articles: Union[int, str], mode: str = None):
        # Determine mode and max_articles
        if isinstance(mode_or_articles, int):
            self.max_articles = mode_or_articles
            self.mode = mode if mode else "rag"
        elif isinstance(mode_or_articles, str):
            if mode_or_articles.lower() in ["direct", "rag"]:
                self.mode = mode_or_articles.lower()
                self.max_articles = 5  # default
            else:
                raise ValueError("If passing a string, must be 'direct' or 'rag'")
        else:
            raise ValueError("First argument must be int (number of articles) or str ('direct' or 'rag')")

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
        if self.mode == "direct":
            self.rag_prompt = PromptTemplate(
                input_variables=["question", "context"],
                template="""
                You are a helpful AI assistant. Answer the following question to the best of your ability.

                Question: {question}

                Answer:"""
            )
        else:
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

        # Build the LangGraph orchestration
        builder = StateGraph(State)
        if self.mode == "direct":
            # Only generate step, no retrieve
            builder.add_node("generate", lambda state: generate(state, self))
            builder.add_edge(START, "generate")
            self.graph = builder.compile(name="direct_pipeline")
        else:
            builder.add_sequence([
                retrieve,
                lambda state: generate(state, self)
            ])
            builder.add_edge(START, "retrieve")
            self.graph = builder.compile(name="rag_pipeline")

    def answer_question(self, question: str) -> Dict[str, Any]:
        try:
            if self.mode == "direct":
                # No retrieval, just LLM
                state = {"question": question, "context": [], "answer": ""}
                result_state = self.graph.invoke(state)
                answer = result_state["answer"]
                docs: List[Document] = []
            else:
                result_state = self.graph.invoke({"question": question})
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
            logging.error(f"Pipeline2 failed: {e}")
            return {
                "question": question,
                "answer": f"Error: {e}",
                "context": [],
                "articles_used": 0
            }

    def close(self):
        """Release resources (best effort, for future extensibility)."""
        self.llm = None
        self.anthropic = None

# === Example usage ===
if __name__ == "__main__":
    # Example: direct mode
    app_direct = Pipeline2Application("direct")
    res_direct = app_direct.answer_question("Give me the latest on news corp columnist Lucy Zelić.")
    print(f"\n[Direct] Question: {res_direct['question']}")
    print(f"Answer: {res_direct['answer']}")
    print(f"Articles used: {res_direct['articles_used']}")
    print("-" * 60)
    app_direct.close()

    # Example: rag mode
    app_rag = Pipeline2Application(5)
    res_rag = app_rag.answer_question("Give me the latest on news corp columnist Lucy Zelić.")
    print(f"\n[RAG] Question: {res_rag['question']}")
    print(f"Answer: {res_rag['answer']}")
    print(f"Articles used: {res_rag['articles_used']}")
    print("-" * 60)
    app_rag.close()
