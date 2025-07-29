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
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_metrics import LangchainMetrics
from langchain_core.callbacks.base import BaseCallbackHandler

load_dotenv()

POST_ENDPOINT_URL = "http://{hostname}:{port}/upload-articles"

# 1. Define the shared state for orchestration
class Database(Enum):
    CLICKHOUSE = ("clickhouse", 8000)
    POSTGRES = ("postgres", 8001)
    CASSANDRA = ("cassandra", 8003)


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
    hostname = "localhost" if os.getenv("LOCAL_STREAMLIT_SERVER", False) else "host.docker.internal"
    docs = requests.get(f"http://{hostname}:{state.get('port')}/related-articles?query={state['question']}").json()
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
    # # build context string
    """IF YOU WANT TO USE THE LLM, SET USE_LLM TO TRUE IN THE .ENV FILE"""
    ctx = "\n\n".join(
        f"Title: {doc.metadata['title']}\n"
        f"Date: {doc.metadata['publication_date']}\n"
        f"Content: {doc.page_content}"
        for doc in state["context"]
    )
    prompt_str = app.rag_prompt.format(question=state["question"], context=ctx)
    if (os.getenv("USE_LLM", "false") == "true"):
        response = app.llm.invoke(prompt_str)
        return {"answer": response.content}
    else:
        return {"answer": "This is a placeholder answer. Replace with actual generation logic."}

def post(state: State, endpoint_url=None):
    """Post results to the specified endpoint"""
    """IF YOU WANT TO USE THE POST STEP, SET USE_POST TO TRUE IN THE .ENV FILE"""
    if (os.getenv("USE_POST", "false") == "true"):
        if not endpoint_url:
            hostname = "localhost" if os.getenv("LOCAL_STREAMLIT_SERVER", False) else "host.docker.internal"
            endpoint_url = POST_ENDPOINT_URL.format(port=state.get('port', 8000), hostname=hostname)
        
        try:
            response = requests.post(
                endpoint_url,
                json={},
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return {"status": "success", "response": response.json() if response.content else {}}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}
    else:
        return {"status": "success", "response": {"message": "Post step executed successfully"}}


class RAGApplication:
    def __init__(self, name: str, max_articles: int = 5):
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
                                              "port": Database[database.upper()].value[1],
                                              "config": {"tags": [f"{database}"]}})
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
