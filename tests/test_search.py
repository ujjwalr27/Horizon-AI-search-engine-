import asyncio
import os
from search import OptimizedSearch
from dotenv import load_dotenv

async def test_search():
    # Load environment variables
    load_dotenv()
    
    # Print API credentials (redacted for security)
    search_key = os.getenv('GOOGLE_SEARCH_KEY')
    search_id = os.getenv('GOOGLE_SEARCH_ID')
    print(f"Search Key configured: {'Yes' if search_key else 'No'}")
    print(f"Search ID configured: {'Yes' if search_id else 'No'}")
    
    try:
        # Initialize search
        search = OptimizedSearch()
        
        # Test query
        query = "dr strange"
        print(f"\nTesting search with query: {query}")
        
        # Perform search
        results = await search.search(query)
        
        # Print results
        print(f"\nResults found: {len(results)}")
        if not results.empty:
            print("\nFirst result:")
            print(f"Title: {results.iloc[0]['title']}")
            print(f"Link: {results.iloc[0]['link']}")
            print(f"Snippet: {results.iloc[0]['snippet'][:100]}...")
        else:
            print("No results found!")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_search())