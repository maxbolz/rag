from enum import Enum
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


POST_ENDPOINT_URL = "http://0.0.0.0:8000/upload-articles"

# 1. Define the shared state for orchestration
class Database(Enum):
    CLICKHOUSE = ("clickhouse", 8000)
    POSTGRES = ("postgres", 8001)


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    port: int


# 2. Step 1: retrieve relevant articles
def retrieve(state: State) -> Dict[str, Any]:
    docs = requests.get(f"http://localhost:{state.get("port", 8000)}/related-articles?query={state['question']}").json()
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
def generate(state: State, app: "RAGApplication") -> Dict[str, Any]:
    # build context string
    ctx = "\n\n".join(
        f"Title: {doc.metadata['title']}\n"
        f"Date: {doc.metadata['publication_date']}\n"
        f"Content: {doc.page_content}"
        for doc in state["context"]
    )
    prompt_str = app.rag_prompt.format(question=state["question"], context=ctx)
    response = app.llm.invoke(prompt_str)
    return {"answer": response.content}
    #return {"answer": "This is a placeholder answer. Replace with actual generation logic."}

def post(data, endpoint_url=None):
    """Post results to the specified endpoint"""
    if not endpoint_url:
        endpoint_url = POST_ENDPOINT_URL
    
    try:
        response = requests.post(
            endpoint_url,
            json=data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return {"status": "success", "response": response.json() if response.content else {}}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}


class RAGApplication:
    def __init__(self, name: str, max_articles: int = 5):
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
        builder = StateGraph(State).add_sequence([
            post,
            retrieve,
            lambda state: generate(state, self)
        ])
        builder.add_edge(START, "post")
        self.graph = builder.compile(name=name)


    def answer_question(self, question: str, database: str) -> Dict[str, Any]:
        """Invoke the orchestrated RAG graph in one call."""
        try:
            # run through retrieve → generate
            if database not in [db.value[0] for db in Database]:
                raise ValueError(f"Invalid database: {database}. Must be one of {[db.value[0] for db in Database]}.")
            
            result_state = self.graph.invoke({"question": question,
                                              "port": Database[database.upper()].value[1]})
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
