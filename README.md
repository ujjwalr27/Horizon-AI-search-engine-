# Horizon Search Engine 🚀

A sophisticated, AI-enhanced search engine built with Python, featuring real-time caching, semantic search, and machine learning-based result ranking. Designed for high performance, reliability, and intelligent search capabilities.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask Version](https://img.shields.io/badge/flask-2.3.2-green.svg)
![Redis Version](https://img.shields.io/badge/redis-5.0.8-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
---

## 🌟 Core Features

### 1. Intelligent Search Architecture
- **Semantic Search**: Advanced text similarity using TF-IDF vectorization.
- **ML-Based Ranking**: Smart result prioritization using machine learning.
- **RAG Integration**: AI-powered snippet generation and summarization.
- **Real-time Relevance Tracking**: Dynamic result ranking based on user interactions.

### 2. High-Performance Infrastructure
- **Async Operations**: Built on asyncio for non-blocking performance.
- **Redis Caching**: Advanced caching with automatic invalidation.
- **Supabase Integration**: Reliable PostgreSQL-based data persistence.
- **Connection Pooling**: Optimized resource management.

### 3. Advanced Result Processing
- **Content Analysis**: Intelligent content extraction and processing.
- **Time-Based Filtering**: Configurable time-based result filtering.
- **Click Tracking**: User interaction monitoring.
- **Relevance Feedback**: Continuous result improvement.

---

## 🛠️ Technical Architecture

### Component Overview
```plaintext
Horizon Search/
├── Core Components
│   ├── App Core (app.py)
│   ├── Search Engine (search.py)
│   └── Result Processing (filter.py)
├── Data Layer
│   ├── Redis Cache (adaptive_cache.py)
│   └── Supabase Storage (storage.py)
├── ML Components
│   ├── Semantic Search (semantic_search.py)
│   ├── ML Ranking (ml_ranking.py)
│   └── RAG Model (rag_model.py)
└── Configuration
    ├── Settings (settings.py)
    └── Logging (logging_config.py)
```
## 🚀 Quick Start
### Prerequisites
- Python 3.8+
- Redis Server
- Supabase Account
- Google Custom Search API credentials

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/horizon-search.git
cd horizon-search
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3.Configure environment variables:
```bash
# Core Configuration
GOOGLE_SEARCH_KEY=your_google_api_key
GOOGLE_SEARCH_ID=your_search_engine_id

# Redis Configuration
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_USER=default
REDIS_PASS=your_redis_password

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Application Settings
PORT=5000
```
4. Run the application:
```
python app.py
```
## 🎯 Key Features Detailed
### 1. Intelligent Search Processing
- Asynchronous Google Custom Search integration.
- Content extraction and analysis.
- RAG-enhanced snippet generation.
- ML-based result ranking.
### 2. Advanced Caching System
- Intelligent cache key management.
- Automatic cache invalidation.
- Error resilient operations.
- Connection pool management.
### 3. Data Persistence
- Supabase integration for reliable storage.
- Click tracking and analytics.
- Time-based result filtering.
- Relevance feedback storage.
### 4. ML Components
- TF-IDF based semantic search.
- Machine learning ranking system.
- RAG model integration.
- Real-time content analysis.
  
## 📈 Performance Features
- Async Operations: Non-blocking I/O throughout.
- Connection Pooling: Optimized resource usage.
- Caching Strategy: Multi-layer caching system.
- Error Resilience: Comprehensive error handling.
- Resource Management: Automatic cleanup and recovery

## 🔍 API Endpoints
### Search
### GET 
```/search?query=your_search_term&time_filter=day```
### Mark Relevant 
POST ```/mark-relevant```
```json
{
    "query": "search_term",
    "link": "result_url",
    "title": "result_title"
}
```
## 📊 Monitoring and Logging
- Comprehensive logging system.
- Performance monitoring.
- Error tracking.
- Analytics collection.

## 🤝 Contributing
Contributions are welcome! Please:

- Fork the repository.
- Create a feature branch:
```bash
git checkout -b feature-name
```

- Commit your changes
```bash
 git commit -m 'Add feature-name'
```
- Push to your branch:
```bash
git push origin feature-name
```
- Submit a pull request.



