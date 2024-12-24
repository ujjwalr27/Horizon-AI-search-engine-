# storage.py

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
import pandas as pd
from settings import SUPABASE_URL, SUPABASE_KEY
from logging_config import get_module_logger

class OptimizedDBStorage:
    def __init__(self):
        self.logger = get_module_logger("storage")
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Ensure the results table exists with proper schema."""
        try:
            # Check if table exists by attempting to select
            response = self.supabase.table("results").select("*").limit(1).execute()
            self.logger.info("Results table exists")
            
        except Exception as e:
            self.logger.error(f"Table check error: {e}")
            # Table might not exist, try to create it using REST API
            try:
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS results (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    query TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    link TEXT NOT NULL,
                    title TEXT NOT NULL,
                    snippet TEXT,
                    created TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
                    relevance BOOLEAN DEFAULT FALSE,
                    ml_rank REAL DEFAULT 0.0,
                    rag_summary TEXT,
                    click_count INTEGER DEFAULT 0,
                    last_clicked TIMESTAMP WITH TIME ZONE,
                    UNIQUE(query, link)
                );
                """
                # Use RPC call instead of raw query
                self.supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
                self.logger.info("Created results table")
            except Exception as create_error:
                self.logger.error(f"Table creation error: {create_error}")
                raise

    async def update_relevance(self, query: str, link: str, result_data: Dict[str, Any]) -> Optional[Dict]:
        """Update relevance and click metrics for a search result."""
        try:
            now = datetime.utcnow().isoformat()
            
            # First check if the record exists
            existing = self.supabase.table("results")\
                .select("*")\
                .eq("query", query)\
                .eq("link", link)\
                .execute()

            if existing and existing.data:
                # Update existing record
                update_data = {
                    "relevance": True,
                    "last_clicked": now,
                    "click_count": existing.data[0].get('click_count', 0) + 1,
                    "title": result_data.get('title'),
                    "snippet": result_data.get('snippet'),
                    "ml_rank": result_data.get('ml_rank'),
                    "rag_summary": result_data.get('rag_summary')
                }
                
                response = self.supabase.table("results")\
                    .update(update_data)\
                    .eq("query", query)\
                    .eq("link", link)\
                    .execute()
                
                if response and response.data:
                    return response.data[0]
            else:
                # Insert new record
                insert_data = {
                    "query": query,
                    "link": link,
                    "relevance": True,
                    "click_count": 1,
                    "last_clicked": now,
                    "rank": result_data.get("rank", 1),
                    "title": result_data.get("title", ""),
                    "snippet": result_data.get("snippet", ""),
                    "ml_rank": result_data.get("ml_rank", 0.0),
                    "rag_summary": result_data.get("rag_summary", ""),
                    "created": now
                }
                
                response = self.supabase.table("results")\
                    .insert(insert_data)\
                    .execute()
                
                if response and response.data:
                    return response.data[0]

            return None

        except Exception as e:
            self.logger.error(f"Update relevance error: {e}")
            return None

    def query_results(self, query: str, time_filter: str = None) -> pd.DataFrame:
        """Query results with time filtering."""
        try:
            base_query = self.supabase.table("results")\
                .select("*")\
                .eq("query", query)

            if time_filter:
                now = datetime.utcnow()
                if time_filter == 'day':
                    cutoff = now - timedelta(days=1)
                elif time_filter == 'month':
                    cutoff = now - timedelta(days=30)
                elif time_filter == 'year':
                    cutoff = now - timedelta(days=365)
                
                base_query = base_query.gte('created', cutoff.isoformat())

            response = base_query\
                .order('relevance', desc=True)\
                .order('click_count', desc=True)\
                .order('rank')\
                .execute()
            
            if response and response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Query error: {e}")
            return pd.DataFrame()

    def insert_or_update_result(self, values: Dict[str, Any]) -> Optional[Dict]:
        """Insert or update a result."""
        try:
            required_fields = ["query", "rank", "link", "title"]
            if not all(field in values for field in required_fields):
                raise ValueError("Missing required fields")

            row_data = {
                "query": values["query"],
                "rank": values["rank"],
                "link": values["link"],
                "title": values["title"],
                "snippet": values.get("snippet", ""),
                "created": datetime.utcnow().isoformat(),
                "relevance": values.get("relevance", False),
                "ml_rank": values.get("ml_rank", 0.0),
                "rag_summary": values.get("rag_summary", ""),
                "click_count": values.get("click_count", 0),
                "last_clicked": values.get("last_clicked")
            }

            response = self.supabase.table("results")\
                .upsert(row_data)\
                .execute()
            
            if response and response.data:
                return response.data[0]
            return None

        except Exception as e:
            self.logger.error(f"Insert/Update error: {e}")
            return None

    async def close(self):
        """Cleanup resources."""
        try:
            # Supabase client doesn't require explicit closing
            pass
        except Exception as e:
            self.logger.error(f"Close error: {e}")