from fastapi import FastAPI

from llm_services.langchain_pipeline import RAGApplication

app = FastAPI()

langchain_pipeline = RAGApplication()

@app.get("/answer-question")
def run(query: str):
    langchain_pipeline.answer_question(query)