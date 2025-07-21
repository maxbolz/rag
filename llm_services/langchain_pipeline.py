import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from clickhouse_services.clickhouse_dao import ClickhouseDao
import logging
from pydantic import SecretStr

load_dotenv()

class RAGApplication:
    def __init__(self):
        # Initialize Anthropic client
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Initialize LangChain ChatAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.llm = ChatAnthropic(
            model_name="claude-3-sonnet-20240229",
            api_key=SecretStr(api_key),
            temperature=0.1,
            timeout=60,
            stop=[]
        )
        
        # Initialize ClickHouse DAO
        self.clickhouse_dao = ClickhouseDao()
        
        # Define RAG prompt
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
    
    def retrieve_relevant_articles(self, question: str, limit: int = 5) -> List[Document]:
        """Retrieve relevant articles from ClickHouse vector database"""
        try:
            # Search for similar articles
            results = self.clickhouse_dao.related_articles(question, limit)
            
            # Convert results to LangChain Documents
            documents = []
            for result in results:
                # Assuming result structure: [url, title, body, publication_date, distance]
                if len(result) >= 3:
                    doc = Document(
                        page_content=result[2],  # body content
                        metadata={
                            "url": result[0],
                            "title": result[1],
                            "publication_date": result[3] if len(result) > 3 else "",
                            "similarity_score": result[4] if len(result) > 4 else 0
                        }
                    )
                    documents.append(doc)
            
            return documents
        except Exception as e:
            logging.error(f"Error retrieving articles: {e}")
            return []
    
    def generate_answer(self, question: str, context_docs: List[Document]) -> str:
        """Generate answer using Claude LLM"""
        try:
            # Prepare context from documents
            context_content = "\n\n".join([
                f"Title: {doc.metadata.get('title', 'Unknown')}\n"
                f"Date: {doc.metadata.get('publication_date', 'Unknown')}\n"
                f"Content: {doc.page_content}"
                for doc in context_docs
            ])
            
            # Create prompt with question and context
            prompt = self.rag_prompt.format(
                question=question,
                context=context_content
            )
            
            # Generate response using Claude
            response = self.llm.invoke(prompt)
            
            return str(response.content)
            
        except Exception as e:
            logging.error(f"Error generating answer: {e}")
            return f"Sorry, I encountered an error while generating the answer: {str(e)}"
    
    def answer_question(self, question: str, max_articles: int = 5) -> Dict[str, Any]:
        """Main RAG pipeline: retrieve relevant articles and generate answer"""
        try:
            # Step 1: Retrieve relevant articles
            relevant_docs = self.retrieve_relevant_articles(question, max_articles)
            
            if not relevant_docs:
                return {
                    "answer": "I couldn't find any relevant articles to answer your question. Please try rephrasing your question.",
                    "context": [],
                    "question": question
                }
            
            # Step 2: Generate answer using Claude
            answer = self.generate_answer(question, relevant_docs)
            
            # Step 3: Prepare response
            response = {
                "answer": answer,
                "context": [
                    {
                        "title": doc.metadata.get("title", "Unknown"),
                        "url": doc.metadata.get("url", ""),
                        "publication_date": doc.metadata.get("publication_date", ""),
                        "similarity_score": doc.metadata.get("similarity_score", 0),
                        "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    for doc in relevant_docs
                ],
                "question": question,
                "articles_used": len(relevant_docs)
            }
            
            return response
            
        except Exception as e:
            logging.error(f"Error in RAG pipeline: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "context": [],
                "question": question,
                "error": str(e)
            }

# Example usage
def main():
    # Initialize RAG application
    rag_app = RAGApplication()
    
    # Example questions
    questions = [
        "What are the latest developments in climate change?",
        "How is the economy performing?",
        "What's happening in technology news?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        result = rag_app.answer_question(question)
        print(f"Answer: {result['answer']}")
        print(f"Articles used: {result['articles_used']}")
        print("-" * 50)

if __name__ == "__main__":
    main() 