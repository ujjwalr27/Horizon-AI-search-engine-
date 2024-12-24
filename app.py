import os
import asyncio
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
import pandas as pd

# Load environment variables
load_dotenv()

# Import optimized modules
from logging_config import setup_logging, get_module_logger
from search import OptimizedSearch
from storage import OptimizedDBStorage
from filter import OptimizedFilter
from ml_ranking import SimplifiedMLRanker
from adaptive_cache import RenderRedisCache
from semantic_search import SemanticSearch

# Configure logging
logger = setup_logging()
search_logger = get_module_logger('search')
ml_logger = get_module_logger('ml_ranking')

class OptimizedSearchApp:
    def __init__(self):
    # Initialize Flask App
         self.app = Flask(__name__)
         CORS(self.app)

    # Initialize components with error handling
         try:
             self.db_storage = OptimizedDBStorage()
             self.adaptive_cache = RenderRedisCache()
             self.ml_ranker = SimplifiedMLRanker()
             self.semantic_search = SemanticSearch()
             self.search_engine = OptimizedSearch()
     
             # Setup routes AFTER initializing components
             self.setup_routes()
     
             logger.info("OptimizedSearchApp initialized successfully")
         except Exception as e:
             logger.error(f"Initialization error: {e}")
             logger.error(traceback.format_exc())
             raise
     
    def setup_routes(self):
        
         self.app.route('/', methods=['GET', 'POST'])(self.index)
         self.app.route('/search', methods=['GET'])(self.search_results)
         self.app.route('/mark-relevant', methods=['POST'])(self.mark_relevant)
         self.app.route('/semantic-search', methods=['POST'])(self.perform_semantic_search)
     
         self.app.errorhandler(404)(self.not_found)
         self.app.errorhandler(500)(self.server_error)

    def _format_results(self, raw_results, query):
        """Format raw search results into template-compatible structure"""
        formatted_results = []

        try:
            # Handle DataFrame results
            if isinstance(raw_results, pd.DataFrame):
                raw_results = raw_results.to_dict('records')

            # Handle list results
            for idx, result in enumerate(raw_results, 1):
                formatted_result = {
                    'rank': idx,
                    'title': result.get('title', 'Untitled'),
                    'link': result.get('url', result.get('link', '#')),
                    'snippet': result.get('snippet', result.get('description', 'No description available')),
                    'ml_rank': result.get('score', result.get('ml_rank', 0.0)),
                    'rag_summary': result.get('summary', result.get('rag_summary', None)),
                    'click_count': result.get('click_count', 0),
                    'relevance': result.get('relevance', False)
                }
                formatted_results.append(formatted_result)

            search_logger.info(f"Formatted {len(formatted_results)} results successfully")
            if formatted_results:
                search_logger.info(f"Sample formatted result: {formatted_results[0]}")

        except Exception as e:
            search_logger.error(f"Error formatting results: {e}")
            search_logger.error(f"Raw results: {raw_results}")
            search_logger.error(traceback.format_exc())

        return formatted_results

    # app.py - Update the _optimized_search_pipeline method

    async def _optimized_search_pipeline(self, query):
        """Async optimized search pipeline with error handling"""
        try:
        # Check cache first
            cached_results = await self.adaptive_cache.async_get(query)
            if cached_results:
                search_logger.info(f"Cache hit for query: {query}")
                return cached_results

        # Perform search
            search_logger.info(f"Performing search for query: {query}")
            raw_results = await self.search_engine.search(query)

        # Debug log the raw results
            search_logger.info(f"Raw results type: {type(raw_results)}")
            search_logger.info(f"Raw results: {raw_results}")

        # Check if raw_results is a DataFrame and handle appropriately
            if isinstance(raw_results, pd.DataFrame):
                if not raw_results.empty:
                    formatted_results = self._format_results(raw_results, query)
                else:
                    formatted_results = []
            else:
            # If raw_results is a list or other type
                formatted_results = self._format_results(raw_results, query)

        # Cache formatted results if they exist
            if formatted_results:
                await self.adaptive_cache.async_put(query, formatted_results)

            search_logger.info(f"Search pipeline completed with {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            search_logger.error(f"Search pipeline error: {e}")
            search_logger.error(traceback.format_exc())
            return []

# Update the search_results method as well
    async def search_results(self):
        """Async search results route with time filtering"""
        query = request.args.get('query', '').strip()
        time_filter = request.args.get('time_filter')
    
        if not query:
            return redirect(url_for('index'))

        try:
        # Log the start of the search
            search_logger.info(f"Starting search for query: {query} with time filter: {time_filter}")
        
        # First check cached results with time filter
            cache_key = f"{query}:{time_filter}" if time_filter else query
            cached_results = await self.adaptive_cache.async_get(cache_key)
        
            if cached_results:
                search_logger.info(f"Cache hit for query: {cache_key}")
                return render_template(
                    'results.html',
                    query=query,
                    results=cached_results,
                    time_filter=time_filter
                )

        # Check database for previous relevant results
            db_results = self.db_storage.query_results(query, time_filter)
        
        # If we have relevant results, combine them with new search results
            if isinstance(db_results, pd.DataFrame) and not db_results.empty:
                search_logger.info(f"Found {len(db_results)} existing relevant results")
            
            # Get new search results
                new_results = await self._optimized_search_pipeline(query)
            
            # Convert new_results to DataFrame if it's a list
                if isinstance(new_results, list):
                    new_results = pd.DataFrame(new_results)
            
            # Combine and deduplicate results
                all_results = self._merge_results(db_results, new_results)
            else:
            # If no existing results, just get new search results
                all_results = await self._optimized_search_pipeline(query)

        # Format results for template
            formatted_results = self._format_results(all_results, query)
        
        # Cache the results if we have any
            if formatted_results:
                await self.adaptive_cache.async_put(cache_key, formatted_results)

            search_logger.info(f"Search completed with {len(formatted_results)} results")
            return render_template(
                'results.html',
                query=query,
                results=formatted_results,
                time_filter=time_filter
            )

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            logger.error(traceback.format_exc())
            return render_template('error.html', error=str(e)), 500

# Update the _merge_results method to handle different input types
    def _merge_results(self, db_results: pd.DataFrame, new_results: pd.DataFrame) -> pd.DataFrame:
        """Merge and deduplicate database and new search results."""
        try:
        # Handle empty DataFrames
            if isinstance(new_results, pd.DataFrame) and new_results.empty:
                return db_results
        
            if isinstance(db_results, pd.DataFrame) and db_results.empty:
                return new_results if isinstance(new_results, pd.DataFrame) else pd.DataFrame(new_results)

        # Convert new_results to DataFrame if it's a list
            if isinstance(new_results, list):
                new_results = pd.DataFrame(new_results)

        # Ensure both DataFrames have the same columns
            required_columns = ['title', 'link', 'snippet', 'ml_rank']
            for df in [db_results, new_results]:
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None

        # Mark the source of results
            db_results['source'] = 'db'
            new_results['source'] = 'new'

        # Combine results and drop duplicates
            combined = pd.concat([db_results, new_results], ignore_index=True)
            combined = combined.drop_duplicates(subset=['link'], keep='first')

        # Ensure numeric columns exist and are properly typed
            combined['click_count'] = combined.get('click_count', 0).fillna(0).astype(float)
            combined['relevance'] = combined.get('relevance', False).fillna(False)
            combined['ml_rank'] = combined.get('ml_rank', 0.0).fillna(0.0).astype(float)

        # Calculate final rank score
            combined['rank_score'] = (
                (combined['relevance'].astype(int) * 2) +
                (combined['click_count'] / combined['click_count'].max() if combined['click_count'].max() > 0 else 0) +
                (combined['ml_rank'] / combined['ml_rank'].max() if combined['ml_rank'].max() > 0 else 0)
            )

        # Sort by rank score
            combined = combined.sort_values('rank_score', ascending=False)
            combined['rank'] = range(1, len(combined) + 1)

            return combined

        except Exception as e:
            logger.error(f"Error merging results: {e}")
        # Return whichever result set is not empty, or an empty DataFrame
            if isinstance(db_results, pd.DataFrame) and not db_results.empty:
                return db_results
            elif isinstance(new_results, pd.DataFrame) and not new_results.empty:
                return new_results
            elif isinstance(new_results, list) and new_results:
                return pd.DataFrame(new_results)
            else:
                return pd.DataFrame()
    async def mark_relevant(self):
        """Enhanced relevance marking with result data storage"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400

            required_fields = ['query', 'link', 'title']
            if not all(field in data for field in required_fields):
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields'
               }), 400

        # Prepare result data with all fields
            result_data = {
                'title': data['title'],
                'snippet': data.get('snippet', ''),
                'ml_rank': float(data.get('ml_rank', 0.0)),
                'rag_summary': data.get('rag_summary', ''),
                'rank': int(data.get('rank', 1))  # Add rank field
            }

        # Update result in database with proper await
            result = await self.db_storage.update_relevance(
                query=data['query'],
                link=data['link'],
                result_data=result_data
            )

            if result is None:
                raise ValueError("Failed to update relevance")

        # Invalidate related caches
            cache_keys = [
                data['query'],
                f"{data['query']}:day",
                f"{data['query']}:month",
                f"{data['query']}:year"
            ]
        
            for key in cache_keys:
                await self.adaptive_cache.async_delete(key)

            return jsonify({
                'status': 'success',
                'data': {
                    'query': data['query'],
                    'link': data['link'],
                    'title': result_data['title'],
                    'click_count': result.get('click_count', 1) if result else 1,
                    'relevance': True
                }
            })

        except Exception as e:
            logger.error(f"Mark relevant error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500    
    def index(self):
        """Home page route"""
        try:
            if request.method == 'POST':
                query = request.form.get('query', '').strip()
                if query:
                    return redirect(url_for('search_results', query=query))
            return render_template('home.html')
        except Exception as e:
            logger.error(f"Index route error: {e}")
            return render_template('error.html', error=str(e)), 500

    async def perform_semantic_search(self):
        """Optimized semantic search endpoint"""
        try:
            data = request.json
            query = data.get('query', '')
            documents = data.get('documents', [])

            if not query or not documents:
                return jsonify({"error": "Invalid request"}), 400

            similarities = await self.semantic_search.async_semantic_search(query, documents)
            return jsonify({"similarities": similarities.tolist()})
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return jsonify({"error": str(e)}), 500

    def not_found(self, error):
        return render_template('error.html', error="Page not found"), 404

    def server_error(self, error):
        return render_template('error.html', error="Internal server error"), 500

    # Continuing app.py...

    def get_app(self):
        """Return the Flask application instance."""
        return self.app

    async def _cleanup(self):
        """Cleanup resources before shutdown."""
        try:
            if hasattr(self, 'adaptive_cache'):
                await self.adaptive_cache.close()
            if hasattr(self, 'search_engine'):
                await self.search_engine._close_session()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def __del__(self):
        """Destructor to ensure cleanup of resources."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._cleanup())
            else:
                loop.run_until_complete(self._cleanup())
        except Exception as e:
            logger.error(f"Destructor cleanup error: {e}")

# Create application instance


# Create application instance with async support
search_app = OptimizedSearchApp()
app = search_app.get_app()

# Add this for better async support
app.config['ASGI_APPLICATION'] = True

# Keep your main assignment
main = app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)