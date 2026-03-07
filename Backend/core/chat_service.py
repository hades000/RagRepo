"""
Chat service for handling queries and conversational context
"""
from typing import List, Dict, Optional, Tuple
from langchain.schema import Document
from langchain_core.language_models import BaseChatModel
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from config import Config


class ChatService:
    """Handle chat queries and conversation management"""
    
    def __init__(self, llm: BaseChatModel, vector_store: FAISS):
        self.llm = llm
        self.vector_store = vector_store
    
    def create_qa_chain(self) -> ConversationalRetrievalChain:
        """
        Create conversational QA chain.
        
        Returns:
            Configured ConversationalRetrievalChain
        """
        # Custom prompt for food tech domain
        qa_prompt = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""You are a food technology knowledge assistant. 
Use the provided context to answer the question thoroughly and clearly.

Guidelines:
- Provide comprehensive answers with all relevant details from the context
- Use bullet points to organize information when listing multiple items or steps
- For complex topics, include explanations and context
- If the context contains detailed information, include it in your answer
- Be complete rather than brief
Context from documents:
{context}

Chat history:
{chat_history}

Question:
{question}

Answer:"""
        )
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": Config.MAX_CONTEXT_CHUNKS}
            ),
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            condense_question_llm=self.llm
        )
        
        return chain
    
    def process_query(
        self, 
        query: str, 
        chat_history: Optional[List[Tuple[str, str]]]  = None
    ) -> Dict:
        """
        Process a chat query.
        
        Args:
            query: User's question
            chat_history: List of (question, answer) tuples
        
        Returns:
            Dictionary with 'answer' and 'source_documents'
        """
        if chat_history is None:
            chat_history = []
        
        # Create QA chain
        chain = self.create_qa_chain()
        
        # Get response
        result = chain({
            "question": query,
            "chat_history": chat_history
        })
        
        return {
            "answer": result.get("answer", "").strip(),
            "source_documents": result.get("source_documents", [])
        }
    
    def format_sources(self, source_docs: List[Document]) -> List[Dict]:
        """
        Format source documents for API response.
        
        Args:
            source_docs: List of Document objects
        
        Returns:
            List of formatted source dictionaries
        """
        sources = []
        
        for doc in source_docs:
            # Truncate content if too long
            content = doc.page_content
            if len(content) > 400:
                content = content[:400] + "..."
            
            sources.append({
                "content": content,
                "filename": doc.metadata.get("filename", "Unknown"),
                "page": doc.metadata.get("page", None),
                "source": doc.metadata.get("source", "Unknown")
            })
        
        return sources
    
    @staticmethod
    def trim_chat_history(
        history: List[Tuple[str, str]], 
        max_messages: Optional[int] = None
    ) -> List[Tuple[str, str]]:
        """
        Trim chat history to recent messages.
        
        Args:
            history: Full chat history
            max_messages: Maximum messages to keep
        
        Returns:
            Trimmed history
        """
        max_messages = max_messages or Config.MAX_HISTORY_MESSAGES
        return history[-max_messages:] if len(history) > max_messages else history