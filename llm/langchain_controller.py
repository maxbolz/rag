from fastapi import FastAPI

from llm.langchain_pipeline import RAGApplication

app = FastAPI()

langchain_pipeline = RAGApplication()

@app.get("/answer-question")
def run(query: str):
    return langchain_pipeline.answer_question(query)
