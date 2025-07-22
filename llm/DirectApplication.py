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

# 3. Step 2: generate answer with Claude

class DirectApplication:
    def __init__(self, mode_or_articles: Union[int, str], mode: str = None):
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
            You are a helpful AI assistant. Answer the following question to the best of your ability.

            Question: {question}

            Answer:"""
        )

        # Build the LangGraph orchestration
        builder = StateGraph(State)
        builder.add_node("generate", lambda state: self.generate(state, self))
        builder.add_edge(START, "generate")
        self.graph = builder.compile(name="direct")

    def answer_question(self, question: str) -> Dict[str, Any]:
            # No retrieval, just LLM
            state = {"question": question, "context": [], "answer": ""}
            result_state = self.graph.invoke(state)
            answer = result_state["answer"]
            return {
                "question": question,
                "answer": answer,
            }

    def close(self):
        """Release resources (best effort, for future extensibility)."""
        self.llm = None
        self.anthropic = None

    def generate(state: State, app: "DirectApplication") -> Dict[str, Any]:
        ctx = ""
        prompt_str = app.rag_prompt.format(question=state["question"], context=ctx)
        response = app.llm.invoke(prompt_str)
        return {"answer": response.content}

# === Example usage ===
if __name__ == "__main__":
    # Example: direct mode
    app_direct = DirectApplication("direct")
    res_direct = app_direct.answer_question("Give me the latest on news corp columnist Lucy Zelić.")
    print(f"\n[Direct] Question: {res_direct['question']}")
    print(f"Answer: {res_direct['answer']}")
    print(f"Articles used: {res_direct['articles_used']}")
    print("-" * 60)
    app_direct.close()