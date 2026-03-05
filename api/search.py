"""
Search API endpoints for RAG queries
"""
from flask import Blueprint, request, jsonify
from typing import Optional
from core.hybrid_retriever import HybridRetriever
from core.bm25_service import BM25Service
from core.reranker_service import RerankerService
from core.embedding_service import EmbeddingService
from core.llm_provider import LLMProvider
from core.cost_tracker import CostTracker
from core.global_vector_store_manager import GlobalVectorStoreManager
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from utils.response import success_response, error_response
from utils.auth import get_current_user, require_auth

search_bp = Blueprint('search', __name__)

# Global services
vector_store: Optional[FAISS] = None
hybrid_retriever: Optional[HybridRetriever] = None
llm_provider: Optional[LLMProvider] = None
cost_tracker: Optional[CostTracker] = None


def init_search_services():
    """Initialize search services (no Prisma needed)"""
    global vector_store, hybrid_retriever, llm_provider, cost_tracker
    
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        bm25_service = BM25Service()
        reranker_service = RerankerService()
        llm_provider = LLMProvider()
        cost_tracker = CostTracker()  # This initializes the global cost_tracker
        
        # Load global vector store
        vector_store_manager = GlobalVectorStoreManager(
            embeddings=embedding_service.embeddings
        )
        
        if vector_store_manager.exists():
            vector_store, _ = vector_store_manager.load()
            print("✅ Global vector store loaded")
        else:
            print("⚠️ Global vector store not found. Run sync first.")
            vector_store = None
        
        # Load BM25 index
        bm25_loaded = bm25_service.load_index()
        if not bm25_loaded:
            print("⚠️ BM25 index not found. Run sync first.")
        
        # Load reranker model
        reranker_service.load_model()
        
        # Initialize hybrid retriever if vector store exists
        if vector_store:
            hybrid_retriever = HybridRetriever(
                vector_store=vector_store,
                bm25_service=bm25_service,
                reranker_service=reranker_service
            )
            print("✅ Hybrid retriever initialized")
        else:
            hybrid_retriever = None
            
    except Exception as e:
        print(f"❌ Error initializing search services: {e}")
        import traceback
        traceback.print_exc()


@search_bp.route('/search', methods=['POST'])
@require_auth
async def search():
    """
    Main search endpoint using hybrid retrieval.
    
    Request body:
        {
            "query": "user question",
            "top_k": 5,  // optional, default 5
            "rerank": true,  // optional, default true
            "include_sources": true  // optional, default true
        }
    
    Returns:
        {
            "answer": "generated answer",
            "sources": [...],
            "retrieval_method": "hybrid",
            "cost_breakdown": {...}
        }
    """
    try:
        # Get authenticated user from request headers
        user = get_current_user()
        user_id = user.get('id')
        
        if not user_id:
            return error_response("User ID not found", 401)
        
        data = request.get_json()
        
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 5)
        use_rerank = data.get('rerank', True)
        include_sources = data.get('include_sources', True)
        
        if not query:
            return error_response("Query is required", 400)
        
        # Check if services are initialized
        if not hybrid_retriever or not vector_store:
            return error_response("Search not available. Indices not loaded.", 503)
        
        if not llm_provider:
            return error_response("LLM provider not initialized", 503)
        
        if not cost_tracker:
            return error_response("Cost tracker not initialized", 503)
        
        # Stage 1: Retrieve documents using hybrid retrieval
        print(f"🔍 Processing query: {query[:100]}...")
        
        retrieved_docs = hybrid_retriever.retrieve(
            query=query,
            k=20,
            rerank=use_rerank,
            final_k=top_k
        )
        
        if not retrieved_docs:
            return success_response(
                data={
                    'answer': "I couldn't find any relevant information to answer your question.",
                    'sources': [],
                    'retrieval_method': 'hybrid'
                },
                message="No documents found"
            )
        
        # Stage 2: Generate answer using LLM
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a knowledgeable assistant for a food technology company.

Use the provided context to answer the question thoroughly and clearly.

Guidelines:
- Provide comprehensive answers with all relevant details from the context
- Use bullet points to organize information when listing multiple items
- For complex topics, include explanations
- If the context contains detailed information, include it
- If you cannot find the answer in the context, say so clearly
- Always cite which document(s) you're referencing

Context from documents:
{context}

Question: {question}

Answer:"""
        )
        
        prompt_text = qa_prompt.format(context=context, question=query)
        answer = llm_provider.generate(prompt_text)
        
        # Stage 3: Format sources
        sources = []
        if include_sources:
            for idx, doc in enumerate(retrieved_docs):
                doc_id = doc.metadata.get('doc_id')
                sources.append({
                    'content': doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content,
                    'full_content': doc.page_content,  # 🆕 Full passage text
                    'filename': doc.metadata.get('source', 'Unknown'),
                    'page': doc.metadata.get('page'),
                    'source_table': doc.metadata.get('source_table', 'Unknown'),
                    'relevance_score': doc.metadata.get('score', 0),  # 🆕 Add relevance score
                    'metadata': {
                        'project': doc.metadata.get('project', 'Unknown'),
                        'product': doc.metadata.get('product', 'Unknown'),
                        'doc_id': doc_id,
                        'chunk_id': doc.metadata.get('chunk_id'),
                    },
                    # 🆕 View URL (view only, no download)
                    'view_url': f'/api/rag/documents/{doc_id}/view' if doc_id else None,
                    'document_info_url': f'/api/rag/documents/{doc_id}' if doc_id else None,
                })
        
        # Stage 4: Calculate costs and log
        embedding_tokens = CostTracker.estimate_tokens(query)  # Use class method
        
        await cost_tracker.log_query_usage(
            user_id=user_id,
            query=query,
            answer=answer,
            model=llm_provider.model,
            provider=llm_provider.provider,
            embedding_tokens=embedding_tokens
        )
        
        # Get cost breakdown
        input_tokens = CostTracker.estimate_tokens(prompt_text)  # Use class method
        output_tokens = CostTracker.estimate_tokens(answer)  # Use class method
        
        llm_cost = CostTracker.calculate_llm_cost(  # Use class method
            llm_provider.provider,
            llm_provider.model,
            input_tokens,
            output_tokens
        )
        
        embedding_cost = CostTracker.calculate_embedding_cost(  # Use class method
            'openai',
            'text-embedding-3-small',
            embedding_tokens
        )
        
        return success_response(
            data={
                'answer': answer,
                'sources': sources,
                'source_count': len(sources),
                'retrieval_method': 'hybrid_bm25_semantic_reranking' if use_rerank else 'hybrid_bm25_semantic',
                'model_used': f"{llm_provider.provider}:{llm_provider.model}",
                'cost_breakdown': {
                    'llm_cost_inr': llm_cost,
                    'embedding_cost_inr': embedding_cost,
                    'total_cost_inr': llm_cost + embedding_cost,
                    'currency': 'INR'
                },
                'tokens_used': {
                    'input': input_tokens,
                    'output': output_tokens,
                    'embedding': embedding_tokens,
                    'total': input_tokens + output_tokens + embedding_tokens
                }
            },
            message="Query processed successfully"
        )
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Search failed: {str(e)}", 500)


@search_bp.route('/search/similar', methods=['POST'])
@require_auth
async def find_similar():
    """
    Find similar documents (no LLM generation).
    
    Request body:
        {
            "query": "search text",
            "top_k": 10
        }
    
    Returns:
        List of similar documents with metadata
    """
    try:
        # Get authenticated user
        user = get_current_user()
        user_id = user.get('id')
        
        if not user_id:
            return error_response("User ID not found", 401)
        
        data = request.get_json()
        
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        
        if not query:
            return error_response("Query is required", 400)
        
        if not hybrid_retriever:
            return error_response("Search not available", 503)
        
        # Retrieve without LLM generation
        retrieved_docs = hybrid_retriever.retrieve(
            query=query,
            k=20,
            rerank=True,
            final_k=top_k
        )
        
        results = []
        for doc in retrieved_docs:
            results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': doc.metadata.get('score', 0)  # Include relevance score if available
            })
        
        return success_response(
            data={
                'documents': results,
                'count': len(results)
            },
            message=f"Found {len(results)} similar documents"
        )
        
    except Exception as e:
        print(f"❌ Similar search error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Similar search failed: {str(e)}", 500)