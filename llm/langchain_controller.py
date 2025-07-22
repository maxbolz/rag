import time
from fastapi import FastAPI
from llm.RAGApplication import RAGApplication
from llm.DirectApplication import DirectApplication


class LangchainController:
    def __init__(self):
        self.pipeline = RAGApplication()
        self.control = DirectApplication()
        self.app = FastAPI()
        self._register_routes()

    def _register_routes(self):
        @self.app.get("/answer-question")
        def answer_question(query: str):
            return self.answer_question(query)

    def answer_question(self, query: str):
        start_time = time.time()
        answer = self.pipeline.answer_question(query)
        end_time = time.time()
        return answer, round(end_time - start_time, 2)

    def answer_question_control(self, query: str):
        start_time = time.time()
        answer = self.control.answer_question(query)
        end_time = time.time()
        return answer, round(end_time - start_time, 2)
