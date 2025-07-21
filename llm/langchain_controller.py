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
            return self.answer_question(query)

    def answer_question(self, query: str):
        return self.pipeline.answer_question(query)
