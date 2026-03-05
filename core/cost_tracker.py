"""
Cost tracking service for monitoring token usage and costs using asyncpg
"""
from typing import Dict, Optional
from datetime import datetime
import json
from .db import get_db

# Cost calculation constants (USD to INR conversion rate)
USD_TO_INR = 85.0

# Pricing per 1000 tokens (in USD)
LLM_PRICING = {
    'openai': {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-4o': {'input': 0.005, 'output': 0.015},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}
    },
    'gemini': {
        'gemini-pro': {'input': 0.000125, 'output': 0.000375},  # $0.125/1M input, $0.375/1M output
        'gemini-pro-vision': {'input': 0.00025, 'output': 0.0005},  # $0.25/1M input, $0.5/1M output
        'gemini-1.5-pro': {'input': 0.000875, 'output': 0.002625},  # $0.875/1M input, $2.625/1M output (up to 128K)
        'gemini-1.5-flash': {'input': 0.000075, 'output': 0.000225},  # $0.075/1M input, $0.225/1M output
        'gemini-2.5-flash': {'input': 0.00015, 'output': 0.00045},  # $0.15/1M input, $0.45/1M output
        'gemini-2.0-flash': {'input': 0.0001, 'output': 0.0003},  # $0.10/1M input, $0.30/1M output
    }
}

# Embedding pricing per 1000 tokens (in USD)
EMBEDDING_PRICING = {
    'openai': {
        'text-embedding-ada-002': 0.0001,
        'text-embedding-3-small': 0.00002,
        'text-embedding-3-large': 0.00013
    }
}


class CostTracker:
    """Track token usage and costs for RAG operations"""
    
    def __init__(self):
        """Initialize cost tracker"""
        pass
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count from text.
        
        Rule of thumb: 1 token ≈ 4 characters
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)
    
    @staticmethod
    def calculate_llm_cost(
        provider: str, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """
        Calculate LLM cost in INR.
        
        Args:
            provider: LLM provider (e.g., 'openai' or 'gemini')
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Cost in INR
        """
        if provider not in LLM_PRICING:
            return 0.0
        
        # Get model pricing with fallback to first available model
        model_pricing = LLM_PRICING[provider].get(
            model, 
            next(iter(LLM_PRICING[provider].values()))
        )
        
        # Cost per 1000 tokens
        input_cost_usd = (input_tokens / 1000) * model_pricing['input']
        output_cost_usd = (output_tokens / 1000) * model_pricing['output']
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # Convert to INR
        total_cost_inr = total_cost_usd * USD_TO_INR
        
        return round(total_cost_inr, 4)
    
    @staticmethod
    def calculate_embedding_cost(
        provider: str, 
        model: str, 
        token_count: int
    ) -> float:
        """
        Calculate embedding cost in INR.
        
        Args:
            provider: Embedding provider
            model: Model name
            token_count: Token count
            
        Returns:
            Cost in INR
        """
        if provider not in EMBEDDING_PRICING:
            return 0.0
        
        # Get model pricing with fallback
        model_pricing = EMBEDDING_PRICING[provider].get(
            model,
            next(iter(EMBEDDING_PRICING[provider].values()))
        )
        
        # Cost per 1000 tokens
        cost_usd = (token_count / 1000) * model_pricing
        cost_inr = cost_usd * USD_TO_INR
        
        return round(cost_inr, 4)
    
    async def log_query_usage(
        self,
        user_id: str,
        query: str,
        answer: str,
        model: str,
        provider: str = 'openai',
        embedding_tokens: int = 0,
        embedding_model: str = 'text-embedding-3-small',
        embedding_provider: str = 'openai'
    ) -> Optional[str]:
        """
        Log token usage for a query operation.
        
        Args:
            user_id: User ID
            query: Query text
            answer: Answer text
            model: LLM model name
            provider: LLM provider
            embedding_tokens: Number of embedding tokens
            embedding_model: Embedding model name
            embedding_provider: Embedding provider
            
        Returns:
            Created record ID or None
        """
        try:
            # Estimate tokens
            input_tokens = self.estimate_tokens(query)
            output_tokens = self.estimate_tokens(answer)
            total_tokens = input_tokens + output_tokens
            
            # Calculate costs
            llm_cost = self.calculate_llm_cost(
                provider, model, input_tokens, output_tokens
            )
            embedding_cost = self.calculate_embedding_cost(
                embedding_provider, embedding_model, embedding_tokens
            )
            total_cost = llm_cost + embedding_cost
            
            # Generate CUID (simplified version)
            import secrets
            record_id = 'c' + secrets.token_urlsafe(20)[:24]
            
            # Insert usage record
            query_sql = """
                INSERT INTO rag_token_usage (
                    id, user_id, timestamp, query, input_tokens, output_tokens,
                    total_tokens, model_used, provider, llm_cost_inr,
                    embedding_tokens, embedding_cost_inr, total_cost_inr, operation_type
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id
            """
            
            db = get_db()
            usage_id = await db.fetchval(
                query_sql,
                record_id, user_id, datetime.now(), query, input_tokens, output_tokens,
                total_tokens, model, provider, llm_cost,
                embedding_tokens, embedding_cost, total_cost, 'query'
            )
            
            # Update cost summary
            await self._update_cost_summary(user_id, llm_cost, embedding_cost, total_cost)
            
            print(f"💰 Logged query cost: ₹{total_cost:.4f} (LLM: ₹{llm_cost:.4f}, Embedding: ₹{embedding_cost:.4f})")
            return usage_id
            
        except Exception as e:
            print(f"❌ Error logging token usage: {e}")
            return None


    async def get_admin_user_id(self) -> Optional[str]:
        """
        Get an admin user ID from the database.
        Tries to find the first available ADMIN user.
        
        Returns:
            Admin user ID or None if no admin found
        """
        try:
            query = """
                SELECT id FROM "User" 
                WHERE role = 'ADMIN' AND "isDeleted" = false 
                ORDER BY "createdAt" ASC 
                LIMIT 1
            """
            db = get_db()
            admin_id = await db.fetchval(query)
            
            if admin_id:
                print(f"✅ Using admin user for cost tracking: {admin_id}")
            else:
                print("⚠️ No admin user found for cost tracking")
            
            return admin_id
            
        except Exception as e:
            print(f"❌ Error finding admin user: {e}")
            return None

    async def resolve_user_id(self, user_id: Optional[str] = None) -> Optional[str]:
        """
        Resolve user ID for cost tracking.
        If user_id is 'system' or None, auto-detect an admin user.
        
        Args:
            user_id: Provided user ID (can be 'system', None, or actual user ID)
            
        Returns:
            Valid user ID or None
        """
        # If specific user provided and not 'system', use it
        if user_id and user_id != 'system':
            return user_id
        
        # Auto-detect admin user
        print("🔍 Auto-detecting admin user for cost tracking...")
        return await self.get_admin_user_id()
    
    async def log_document_sync(
        self,
        user_id: Optional[str] = None,
        document_count: int = 0,
        embedding_tokens: int = 0,
        embedding_model: str = 'text-embedding-3-small',
        embedding_provider: str = 'openai'
    ) -> Optional[str]:
        """
        Log token usage for document sync operation.
        
        Args:
            user_id: User ID (auto-detects admin if None or 'system')
            document_count: Number of documents synced
            embedding_tokens: Tokens used for embeddings
            embedding_model: Embedding model name
            embedding_provider: Embedding provider
            
        Returns:
            Created record ID or None
        """
        try:
            # Resolve user ID
            resolved_user_id = await self.resolve_user_id(user_id)
            if not resolved_user_id:
                print("⚠️ No valid user ID for cost tracking - skipping")
                return None
            
            # Calculate embedding cost
            embedding_cost = self.calculate_embedding_cost(
                embedding_provider, embedding_model, embedding_tokens
            )
            
            # Generate CUID
            import secrets
            record_id = 'c' + secrets.token_urlsafe(20)[:24]
            
            # Insert usage record
            query_sql = """
                INSERT INTO rag_token_usage (
                    id, user_id, timestamp, query, input_tokens, output_tokens,
                    total_tokens, model_used, provider, llm_cost_inr,
                    embedding_tokens, embedding_cost_inr, total_cost_inr, operation_type
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id
            """
            
            db = get_db()
            usage_id = await db.fetchval(
                query_sql,
                record_id, resolved_user_id, datetime.now(), 
                f'Document sync: {document_count} documents', 
                0, 0, embedding_tokens, embedding_model, embedding_provider, 0.0,
                embedding_tokens, embedding_cost, embedding_cost, 'sync'
            )
            
            # Update cost summary
            await self._update_cost_summary(resolved_user_id, 0.0, embedding_cost, embedding_cost)
            
            print(f"💰 Logged sync cost: ₹{embedding_cost:.4f} for {document_count} documents (user: {resolved_user_id})")
            return usage_id
            
        except Exception as e:
            print(f"❌ Error logging sync usage: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _update_cost_summary(
        self, 
        user_id: str, 
        llm_cost: float, 
        embedding_cost: float, 
        total_cost: float
    ):
        """
        Update user's cost summary using UPSERT.
        
        Args:
            user_id: User ID
            llm_cost: LLM cost to add
            embedding_cost: Embedding cost to add
            total_cost: Total cost to add
        """
        try:
            query = """
                INSERT INTO rag_cost_summary (
                    user_id, total_llm_cost_inr, total_embedding_cost_inr, 
                    total_cost_inr, last_updated
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_llm_cost_inr = rag_cost_summary.total_llm_cost_inr + $2,
                    total_embedding_cost_inr = rag_cost_summary.total_embedding_cost_inr + $3,
                    total_cost_inr = rag_cost_summary.total_cost_inr + $4,
                    last_updated = $5
            """
            
            db = get_db()
            await db.execute(
                query,
                user_id, llm_cost, embedding_cost, total_cost, datetime.now()
            )
                
        except Exception as e:
            print(f"❌ Error updating cost summary: {e}")
    
    async def get_user_cost_summary(self, user_id: str) -> Dict:
        """
        Get cost summary for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with cost breakdown
        """
        try:
            # Get summary
            db = get_db()
            summary = await db.fetchrow(
                "SELECT * FROM \"RagCostSummary\" WHERE user_id = $1",
                user_id
            )
            
            if not summary:
                return {
                    'total_cost_inr': 0.0,
                    'total_llm_cost_inr': 0.0,
                    'total_embedding_cost_inr': 0.0,
                    'query_count': 0,
                    'sync_count': 0
                }
            
            # Get operation counts
            counts = await db.fetchrow("""
                SELECT 
                    COUNT(*) FILTER (WHERE operation_type = 'query') as query_count,
                    COUNT(*) FILTER (WHERE operation_type = 'sync') as sync_count
                FROM rag_token_usage
                WHERE user_id = $1
            """, user_id)
            
            return {
                'total_cost_inr': float(summary['total_cost_inr']),
                'total_llm_cost_inr': float(summary['total_llm_cost_inr']),
                'total_embedding_cost_inr': float(summary['total_embedding_cost_inr']),
                'query_count': counts['query_count'] or 0,
                'sync_count': counts['sync_count'] or 0,
                'last_updated': summary['last_updated'].isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting cost summary: {e}")
            return {
                'total_cost_inr': 0.0,
                'total_llm_cost_inr': 0.0,
                'total_embedding_cost_inr': 0.0,
                'query_count': 0,
                'sync_count': 0
            }
    
    async def get_recent_usage(self, user_id: str, limit: int = 10) -> list:
        """
        Get recent token usage records.
        
        Args:
            user_id: User ID
            limit: Number of records to return
            
        Returns:
            List of usage records
        """
        try:
            db = get_db()
            rows = await db.fetch("""
                SELECT 
                    id, timestamp, query, operation_type,
                    input_tokens, output_tokens, total_tokens,
                    model_used, provider, total_cost_inr
                FROM rag_token_usage
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, user_id, limit)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"❌ Error getting recent usage: {e}")
            return []