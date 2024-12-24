
import aiohttp
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional
import json
from urllib.parse import quote_plus
import html
from bs4 import BeautifulSoup
from logging_config import get_module_logger
from settings import (
    SEARCH_KEY,
    SEARCH_ID,
    MAX_SEARCH_RESULTS,
    MAX_CONCURRENT_REQUESTS,
    REQUEST_TIMEOUT
)
from rag_model import SimplifiedRAG

class OptimizedSearch:
    def __init__(self):
        self.logger = get_module_logger('search')
        self.rag_model = SimplifiedRAG()
        
        # Validate API credentials
        if not SEARCH_KEY or not SEARCH_ID:
            self.logger.error("Missing Google Search API credentials")
            raise ValueError("Missing required Google Search API configuration")
            
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.session = None

    async def _init_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def _fetch_search_results(self, query: str, start_index: int = 1) -> Dict:
        """Enhanced search results fetching with detailed error handling"""
        try:
            await self._init_session()
            
            # Build search URL with proper parameters
            params = {
                'key': SEARCH_KEY,
                'cx': SEARCH_ID,
                'q': query,
                'start': start_index,
                'num': 10,  # Number of results per request
                'safe': 'off',  # Don't filter results
                'fields': 'items(title,link,snippet)',  # Only get needed fields
            }
            
            self.logger.info(f"Fetching results for query: {query}")
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'items' not in data:
                        self.logger.warning(f"No results found for query: {query}")
                        return {'items': []}
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Error {response.status}: {error_text}")
                    # Log the actual request URL for debugging
                    self.logger.error(f"Request URL: {response.url}")
                    return {'items': []}
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error during search: {str(e)}")
            return {'items': []}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response: {str(e)}")
            return {'items': []}
        except Exception as e:
            self.logger.error(f"Unexpected error during search: {str(e)}")
            return {'items': []}

    async def _process_search_item(self, item: Dict) -> Dict[str, Any]:
        """Process a single search result with enhanced error handling"""
        try:
            url = item.get('link', '')
            title = html.unescape(item.get('title', ''))
            snippet = html.unescape(item.get('snippet', ''))
            
            # Skip invalid results
            if not url or not title:
                self.logger.warning(f"Skipping invalid result: {item}")
                return None
                
            # Basic content fetch
            content = await self._fetch_page_content(url)
            
            # Generate summary if content exists
            rag_summary = None
            if content:
                rag_summary = await self.rag_model.async_generate_response(
                    query=title,
                    context=snippet
                )
            
            return {
                'title': title,
                'link': url,
                'snippet': snippet,
                'html': content or '',
                'rag_summary': rag_summary,
                'ml_rank': 1.0  # Default ranking
            }
            
        except Exception as e:
            self.logger.error(f"Error processing search result: {str(e)}")
            return None

    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch webpage content with timeout and error handling"""
        try:
            await self._init_session()
            async with self.session.get(
                url,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True
            ) as response:
                if response.status == 200:
                    return await response.text()
                self.logger.warning(f"Failed to fetch content from {url}: Status {response.status}")
                return None
        except Exception as e:
            self.logger.warning(f"Error fetching content from {url}: {str(e)}")
            return None

    async def search(self, query: str) -> pd.DataFrame:
        """Perform search with enhanced error handling and logging"""
        try:
            self.logger.info(f"Starting search for query: {query}")
            
            # Validate query
            if not query.strip():
                self.logger.warning("Empty query provided")
                return pd.DataFrame()
            
            # Fetch results
            response = await self._fetch_search_results(query)
            if not response or 'items' not in response:
                self.logger.warning("No results returned from API")
                return pd.DataFrame()
            
            # Process results
            tasks = []
            for item in response['items'][:MAX_SEARCH_RESULTS]:
                tasks.append(self._process_search_item(item))
            
            # Gather results with concurrency limit
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            async with semaphore:
                results = await asyncio.gather(*tasks)
            
            # Filter out None results and convert to DataFrame
            valid_results = [r for r in results if r is not None]
            if not valid_results:
                self.logger.warning("No valid results after processing")
                return pd.DataFrame()
            
            df = pd.DataFrame(valid_results)
            df['rank'] = range(1, len(df) + 1)
            
            self.logger.info(f"Search completed successfully with {len(df)} results")
            return df
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return pd.DataFrame()
        finally:
            # Always close the session
            if self.session:
                await self._close_session()

    async def _close_session(self):
        """Safely close the aiohttp session"""
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                self.logger.error(f"Error closing session: {str(e)}")
            finally:
                self.session = None