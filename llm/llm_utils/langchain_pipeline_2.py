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
from llm.langchain_metrics import LangchainMetrics
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.runnables import RunnableSequence
from typing_extensions import TypedDict

load_dotenv()


# 1. Define the RAG chain
class RAGChain:
    """Custom RAG chain that combines retrieval and generation."""
    
    def __init__(self, llm: ChatAnthropic, rag_prompt: PromptTemplate):
        self.llm = llm
        self.rag_prompt = rag_prompt
    
    def _retrieve_documents(self, question: str) -> List[Document]:
        """Retrieve relevant documents."""
        if os.getenv("DATABASE_TYPE", "").lower() == "clickhouse":
            port = 8000
        elif os.getenv("DATABASE_TYPE", "").lower() == "postgres":
            port = 8001
        else:
            raise ValueError("DATABASE_TYPE must be either clickhouse or postgres")
        
        docs = requests.get(f"http://localhost:{port}/related-articles?query={question}").json()
        return [
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
    
    def invoke(self, inputs: Dict[str, Any], callbacks=None) -> Dict[str, Any]:
        """Invoke the RAG chain with proper callback handling."""
        question = inputs["question"]
        
        # Step 1: Retrieve documents
        docs = self._retrieve_documents(question)
        
        # Step 2: Generate answer using LLMChain for proper callback support
        ctx = "\n\n".join(
            f"Title: {doc.metadata['title']}\n"
            f"Date: {doc.metadata['publication_date']}\n"
            f"Content: {doc.page_content}"
            for doc in docs
        )
        
        # Create a temporary runnable for the generation step
        runnable = self.rag_prompt | self.llm
        response = runnable.invoke(
            {"question": question, "context": ctx}, 
            config={"callbacks": callbacks}
        )
        
        return {
            "answer": response.content,
            "context": [
                {
                    "title": d.metadata["title"],
                    "url": d.metadata["url"],
                    "publication_date": d.metadata["publication_date"],
                    "similarity_score": d.metadata["similarity_score"],
                    "snippet": (d.page_content[:200] + "...") if len(d.page_content) > 200 else d.page_content
                }
                for d in docs
            ],
            "articles_used": len(docs)
        }

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
        run = langchain_metrics.get_runs_by_id_safe([run_id])
        if run:
            print(f"Found run: {run.trace_id}")
            # Process the run here
            langchain_metrics.save_to_clickhouse(run)
        else:
            print(f"No run found for run_id: {run_id}")

    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, **kwargs):
        print(f"Chain run started with run_id: {run_id}")
        print(f"Inputs: {inputs}")
        self.chain_run_ids.append(run_id)
    
    def on_chain_end(self, outputs, *, run_id, parent_run_id=None, **kwargs):
        print(f"Chain run ended with run_id: {run_id}")
        print(f"Outputs: {outputs}")
        # Process the run here
        import time
        time.sleep(1)  # Give LangSmith time to save the run
        langchain_metrics = LangchainMetrics()
        langchain_metrics.connect_clickhouse()  # Connect to ClickHouse
        run = langchain_metrics.get_runs_by_id_safe([run_id])
        if run:
            print(f"Found run: {run.trace_id}")
            langchain_metrics.save_to_clickhouse(run)
        else:
            print(f"No run found for run_id: {run_id}")
    
    def on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None, **kwargs):
        print(f"LLM run started with run_id: {run_id}")
        self.run_ids.append(run_id)
    
    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kwargs):
        print(f"LLM run ended with run_id: {run_id}")
        self.last_run_id = run_id
        

        

# These functions are now integrated into the RAGChain class


class RAGApplication:
    def __init__(self, max_articles: int = 5):
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
        
        # Create the RAG chain
        self.rag_chain = RAGChain(llm=self.llm, rag_prompt=self.rag_prompt)

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Invoke the RAG chain with callbacks."""
        try:
            collector = RunIdCollector()
            # Invoke the chain with callbacks
            result = self.rag_chain.invoke({"question": question}, callbacks=[collector])
            
            return {
                "question": question,
                "answer": result["answer"],
                "articles_used": result["articles_used"],
                "context": result["context"]
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
        "Give me the latest on Epstein.",
    ]:
        res = state_app.answer_question(q)
