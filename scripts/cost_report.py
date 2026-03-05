"""
Cost Report Generator for RAG System
Generates detailed cost analysis reports from rag_token_usage and rag_cost_summary tables
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import json
import os
from dotenv import load_dotenv

load_dotenv()


class CostReporter:
    """Generate cost reports from RAG token usage data"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=5,
            command_timeout=60
        )
        print("✅ Database pool initialized")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("✅ Database pool closed")
    
    async def get_total_costs(self) -> Dict:
        """Get system-wide total costs"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        query = """
        SELECT 
            COUNT(DISTINCT user_id) as total_users,
            COUNT(*) as total_operations,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(embedding_tokens) as total_embedding_tokens,
            SUM(llm_cost_inr) as total_llm_cost,
            SUM(embedding_cost_inr) as total_embedding_cost,
            SUM(total_cost_inr) as total_cost
        FROM rag_token_usage
        """
        
        row = await self.pool.fetchrow(query)
        
        return {
            'total_users': row['total_users'] or 0,
            'total_operations': row['total_operations'] or 0,
            'total_input_tokens': row['total_input_tokens'] or 0,
            'total_output_tokens': row['total_output_tokens'] or 0,
            'total_tokens': row['total_tokens'] or 0,
            'total_embedding_tokens': row['total_embedding_tokens'] or 0,
            'total_llm_cost_inr': float(row['total_llm_cost'] or 0),
            'total_embedding_cost_inr': float(row['total_embedding_cost'] or 0),
            'total_cost_inr': float(row['total_cost'] or 0)
        }
    
    async def get_costs_by_user(self) -> List[Dict]:
        """Get cost breakdown by user"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        query = """
        SELECT 
            u.id,
            u.name,
            u.email,
            cs.total_llm_cost_inr,
            cs.total_embedding_cost_inr,
            cs.total_cost_inr,
            cs.last_updated,
            COUNT(rtu.id) as operation_count
        FROM users u
        INNER JOIN rag_cost_summary cs ON u.id = cs.user_id
        LEFT JOIN rag_token_usage rtu ON u.id = rtu.user_id
        GROUP BY u.id, u.name, u.email, cs.total_llm_cost_inr, 
                 cs.total_embedding_cost_inr, cs.total_cost_inr, cs.last_updated
        ORDER BY cs.total_cost_inr DESC
        """
        
        rows = await self.pool.fetch(query)
        
        return [
            {
                'user_id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'llm_cost_inr': float(row['total_llm_cost_inr'] or 0),
                'embedding_cost_inr': float(row['total_embedding_cost_inr'] or 0),
                'total_cost_inr': float(row['total_cost_inr'] or 0),
                'operation_count': row['operation_count'],
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None
            }
            for row in rows
        ]
    
    async def get_costs_by_operation_type(self) -> List[Dict]:
        """Get cost breakdown by operation type"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        query = """
        SELECT 
            operation_type,
            COUNT(*) as operation_count,
            SUM(total_tokens) as total_tokens,
            SUM(llm_cost_inr) as total_llm_cost,
            SUM(embedding_cost_inr) as total_embedding_cost,
            SUM(total_cost_inr) as total_cost,
            AVG(total_cost_inr) as avg_cost_per_operation
        FROM rag_token_usage
        GROUP BY operation_type
        ORDER BY total_cost DESC
        """
        
        rows = await self.pool.fetch(query)
        
        return [
            {
                'operation_type': row['operation_type'],
                'operation_count': row['operation_count'],
                'total_tokens': row['total_tokens'] or 0,
                'total_llm_cost_inr': float(row['total_llm_cost'] or 0),
                'total_embedding_cost_inr': float(row['total_embedding_cost'] or 0),
                'total_cost_inr': float(row['total_cost'] or 0),
                'avg_cost_per_operation': float(row['avg_cost_per_operation'] or 0)
            }
            for row in rows
        ]
    
    async def get_costs_by_model(self) -> List[Dict]:
        """Get cost breakdown by LLM model"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        query = """
        SELECT 
            model_used,
            provider,
            COUNT(*) as operation_count,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(llm_cost_inr) as total_cost
        FROM rag_token_usage
        WHERE operation_type IN ('query', 'chat')
        GROUP BY model_used, provider
        ORDER BY total_cost DESC
        """
        
        rows = await self.pool.fetch(query)
        
        return [
            {
                'model': row['model_used'],
                'provider': row['provider'],
                'operation_count': row['operation_count'],
                'total_input_tokens': row['total_input_tokens'] or 0,
                'total_output_tokens': row['total_output_tokens'] or 0,
                'total_cost_inr': float(row['total_cost'] or 0)
            }
            for row in rows
        ]
    
    async def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get daily cost breakdown for last N days"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as operation_count,
            SUM(total_tokens) as total_tokens,
            SUM(llm_cost_inr) as llm_cost,
            SUM(embedding_cost_inr) as embedding_cost,
            SUM(total_cost_inr) as total_cost
        FROM rag_token_usage
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """
        
        rows = await self.pool.fetch(query, days)
        
        return [
            {
                'date': row['date'].isoformat(),
                'operation_count': row['operation_count'],
                'total_tokens': row['total_tokens'] or 0,
                'llm_cost_inr': float(row['llm_cost'] or 0),
                'embedding_cost_inr': float(row['embedding_cost'] or 0),
                'total_cost_inr': float(row['total_cost'] or 0)
            }
            for row in rows
        ]
    
    async def get_top_expensive_queries(self, limit: int = 10) -> List[Dict]:
        """Get most expensive queries"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        query = """
        SELECT 
            u.name as user_name,
            u.email as user_email,
            rtu.query,
            rtu.timestamp,
            rtu.total_tokens,
            rtu.total_cost_inr,
            rtu.model_used,
            rtu.operation_type
        FROM rag_token_usage rtu
        INNER JOIN users u ON rtu.user_id = u.id
        ORDER BY rtu.total_cost_inr DESC
        LIMIT $1
        """
        
        rows = await self.pool.fetch(query, limit)
        
        return [
            {
                'user_name': row['user_name'],
                'user_email': row['user_email'],
                'query': row['query'][:100] + '...' if len(row['query']) > 100 else row['query'],
                'timestamp': row['timestamp'].isoformat(),
                'total_tokens': row['total_tokens'],
                'total_cost_inr': float(row['total_cost_inr']),
                'model': row['model_used'],
                'operation_type': row['operation_type']
            }
            for row in rows
        ]
    
    async def generate_full_report(self, days: int = 30) -> Dict:
        """Generate comprehensive cost report"""
        print("\n" + "="*70)
        print("💰 RAG COST ANALYSIS REPORT")
        print("="*70)
        
        # Total costs
        total_costs = await self.get_total_costs()
        print(f"\n📊 SYSTEM-WIDE TOTALS:")
        print(f"   Total Users: {total_costs['total_users']}")
        print(f"   Total Operations: {total_costs['total_operations']}")
        print(f"   Total Tokens: {total_costs['total_tokens']:,}")
        print(f"   Total LLM Cost: ₹{total_costs['total_llm_cost_inr']:.2f}")
        print(f"   Total Embedding Cost: ₹{total_costs['total_embedding_cost_inr']:.2f}")
        print(f"   TOTAL COST: ₹{total_costs['total_cost_inr']:.2f}")
        
        # Costs by user
        user_costs = await self.get_costs_by_user()
        print(f"\n👥 TOP USERS BY COST:")
        for i, user in enumerate(user_costs[:5], 1):
            print(f"   {i}. {user['name']} ({user['email']})")
            print(f"      Operations: {user['operation_count']}, Cost: ₹{user['total_cost_inr']:.2f}")
        
        # Costs by operation type
        op_costs = await self.get_costs_by_operation_type()
        print(f"\n⚙️  COSTS BY OPERATION TYPE:")
        for op in op_costs:
            print(f"   {op['operation_type'].upper()}: {op['operation_count']} ops, ₹{op['total_cost_inr']:.2f}")
        
        # Costs by model
        model_costs = await self.get_costs_by_model()
        print(f"\n🤖 COSTS BY MODEL:")
        for model in model_costs:
            print(f"   {model['model']} ({model['provider']}): {model['operation_count']} ops, ₹{model['total_cost_inr']:.2f}")
        
        # Daily costs
        daily_costs = await self.get_daily_costs(days)
        print(f"\n📅 DAILY COSTS (Last {days} days):")
        for day in daily_costs[:7]:  # Show last 7 days
            print(f"   {day['date']}: {day['operation_count']} ops, ₹{day['total_cost_inr']:.2f}")
        
        # Top expensive queries
        expensive_queries = await self.get_top_expensive_queries(5)
        print(f"\n💸 TOP 5 EXPENSIVE QUERIES:")
        for i, q in enumerate(expensive_queries, 1):
            print(f"   {i}. {q['user_name']}: ₹{q['total_cost_inr']:.2f}")
            print(f"      Query: {q['query']}")
        
        print("\n" + "="*70)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'totals': total_costs,
            'by_user': user_costs,
            'by_operation': op_costs,
            'by_model': model_costs,
            'daily': daily_costs,
            'top_expensive': expensive_queries
        }
    
    async def save_report_to_file(self, report: Dict, filename: Optional[str] = None):
        """Save report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'rag_cost_report_{timestamp}.json'
        
        # Create reports directory
        reports_dir = Path(__file__).parent.parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        filepath = reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: {filepath}")
        return filepath


async def main():
    """Main execution"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    reporter = CostReporter(database_url)
    
    try:
        # Initialize
        await reporter.initialize()
        
        # Generate report
        report = await reporter.generate_full_report(days=30)
        
        # Save to file
        await reporter.save_report_to_file(report)
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await reporter.close()


if __name__ == '__main__':
    asyncio.run(main())