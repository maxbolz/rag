import time
from fastapi import FastAPI
from langchain_pipeline import RAGApplication


class LangchainController:
    def __init__(self):
        self.pipeline = RAGApplication()
        self.app = FastAPI()
        self._register_routes()

    def _register_routes(self):
        @self.app.get("/answer-question")
        def answer_question(query: str):
            start_time = time.time()
            answer = self.pipeline.answer_question(query)
            end_time = time.time()
            return answer, round(end_time - start_time, 2)
