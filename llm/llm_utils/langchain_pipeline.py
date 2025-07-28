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
<<<<<<< HEAD
from llm.langchain_metrics import LangchainMetrics
from langchain_core.callbacks.base import BaseCallbackHandler
=======
from enum import Enum
>>>>>>> 67719a3242105152268b66ef0a7192122bf13992

# === LangGraph imports ===
from langgraph.graph import StateGraph, START
from typing_extensions import TypedDict

load_dotenv()

class AvailableRAGDatabases(Enum):
    CLICKHOUSE = "clickhouse"
    POSTGRES = "postgres"

PORT_MAPPING = { 
    AvailableRAGDatabases.CLICKHOUSE: 8000,
    AvailableRAGDatabases.POSTGRES: 8001
}

# 1. Define the shared state for orchestration
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

class RunIdCollector(BaseCallbackHandler):
    def __init__(self):
        self.run_ids = []
        self.last_run_id = None  # Add this line
        self.chain_run_ids = []

    def on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None, **kwargs):
        self.run_ids.append(run_id)
        print(f"LLM run started with run_id: {run_id}")
        # Store run_id for later processing in on_llm_end
        self.current_run_id = run_id

    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kwargs):
        print(f"LLM run ended with run_id: {run_id}")
        # Process the run after it's completed
        import time
        time.sleep(1)  # Give LangSmith time to save the run
        langchain_metrics = LangchainMetrics()
        langchain_metrics.connect_clickhouse()  # Connect to ClickHouse
        # run = langchain_metrics.get_runs_by_id_safe([run_id])
        # if run:
        #     # Process the run here
        #     langchain_metrics.save_to_clickhouse(run)
        # else:
        #     print(f"No run found for run_id: {run_id}")
        
        run_name = "retrieve"
        runs = langchain_metrics.get_runs(num_runs=1, run_ids=None, run_name=run_name)
        print(f"Runs: {runs}")
        
        if runs and len(runs) > 0:
            # Get the first run from the list
            run = runs[0]
            print(f"Found run with name: {run.name}")
            #save run to clickhouse
            langchain_metrics.save_to_clickhouse(run)
        else:
            print(f"No run found for run_name: {run_name}")
        

    # def on_chain_start(self, inputs, *, run_id, parent_run_id=None, **kwargs):
    #     print(f"Chain run started with run_id: {run_id}")
    #     self.chain_run_ids.append(run_id)
    
    # def on_chain_end(self, outputs, *, run_id, parent_run_id=None, **kwargs):
    #     print(f"Chain run ended with run_id: {run_id}")
    #     # Process the run here
    #     langchain_metrics = LangchainMetrics()
    #     langchain_metrics.connect_clickhouse()  # Connect to ClickHouse
    #     run = langchain_metrics.get_runs_by_id_safe([run_id])
    #     if run:
    #         print(f"Found run: {run.trace_id}")
        
        
        

        

# 2. Step 1: retrieve relevant articles
def retrieve(state: State) -> Dict[str, Any]:
    # Choose port based on database type
<<<<<<< HEAD
    database_type = os.getenv("DATABASE_TYPE", "")
    print(f"DEBUG: DATABASE_TYPE is '{database_type}'")
    
    if database_type.lower() == "clickhouse":
        port = 8000  # Port from clickhouse docker-compose
        print(f"DEBUG: Using ClickHouse port {port}")
    elif database_type.lower() == "postgres":
        port = 8001  # Port from postgres docker-compose
        print(f"DEBUG: Using PostgreSQL port {port}")
    else:
        raise ValueError(f"DATABASE_TYPE must be either clickhouse or postgres, got '{database_type}'")
=======
    port = PORT_MAPPING[AvailableRAGDatabases(os.getenv("DATABASE_TYPE", "").lower())]
    logging.info(f"Using port {port} for {AvailableRAGDatabases(os.getenv('DATABASE_TYPE', '').lower())}")
>>>>>>> 67719a3242105152268b66ef0a7192122bf13992

    # hostname is based on local machine or docker
    hostname = "localhost" if os.getenv("LOCAL_STREAMLIT_SERVER", False) else "host.docker.internal"
    docs = requests.get(f"http://{hostname}:{port}/related-articles?query={state['question']}").json()
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


class RAGApplication:
    def __init__(self, max_articles: int = 5):
        # — your existing initialization —
        self.max_articles = max_articles
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        collector = RunIdCollector()

        self.llm = ChatAnthropic(
            model_name="claude-3-5-sonnet-latest",
            api_key=SecretStr(api_key),
            temperature=0.1,
            timeout=60,
            stop=[],
            callbacks=[collector]
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
        )        # 4. Build the LangGraph orchestration
        builder = StateGraph(State).add_sequence([
            retrieve,
            lambda state: generate(state, self)
        ])
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
        "Give me the latest on Trump.",
    ]:
        res = state_app.answer_question(q)
