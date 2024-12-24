# test_redis.py
import logging
from adaptive_cache import RenderRedisCache
import os
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_connection():
    """Test Redis connection and basic operations"""
    print("\nTesting Redis Connection...")
    
    try:
        # Initialize cache
        cache = RenderRedisCache()
        
        # Test data
        test_key = "test:connection"
        test_data = {
            "status": "connected",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_value": "Hello Redis!"
        }
        
        # Test PUT
        print("\nTesting PUT operation...")
        put_success = cache.put(test_key, test_data)
        if not put_success:
            print("❌ PUT operation failed")
            return False
        print("✅ PUT operation successful")
        
        # Test GET
        print("\nTesting GET operation...")
        retrieved_data = cache.get(test_key)
        if retrieved_data != test_data:
            print("❌ GET operation failed or data mismatch")
            print(f"Expected: {test_data}")
            print(f"Got: {retrieved_data}")
            return False
        print("✅ GET operation successful")
        print(f"Retrieved  {retrieved_data}")
        
        # Test DELETE
        print("\nTesting DELETE operation...")
        delete_success = cache.delete(test_key)
        if not delete_success:
            print("❌ DELETE operation failed")
            return False
        print("✅ DELETE operation successful")
        
        # Verify deletion
        verification_data = cache.get(test_key)
        if verification_data is not None:
            print("❌ Key still exists after deletion")
            return False
        print("✅ Key successfully deleted")
        
        print("\n✅ All operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False

def print_redis_info():
    """Print Redis configuration and test environment"""
    print("Redis Configuration:")
    print(f"Host: {os.getenv('REDIS_HOST')}")
    print(f"Port: {os.getenv('REDIS_PORT')}")
    print(f"User: {os.getenv('REDIS_USER')}")
    print("-" * 50)

if __name__ == "__main__":
    load_dotenv()
    print_redis_info()
    
    success = test_connection()
    print(f"\nOverall test {'passed ✅' if success else 'failed ❌'}")
