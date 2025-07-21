import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from clickhouse_services.clickhouse_dao import ClickhouseDao
import requests    



class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

def retrieve(state: State):
    response = requests.get(
        "http://localhost:8000/related-articles",
        params={"query": state["question"]}
    )
    
    if response.status_code == 200:
        return {"context": response.json()}
    else:
        return {"context": []}
    

def generate(state: State):
    docs_content = 

# class LangchainDao:

#     def __init__(self, db: str = "clickhouse"):
#         if db == "postgres":
#             self.dao = PostgresDao()
#         elif db == "clickhouse":
#             self.dao = ClickhouseDao()
#         else:
#             raise ValueError("Database must be either 'postgres' or 'clickhouse'")


#     def retrieve(state: State):
#         r

#     def generate(state: State):

    