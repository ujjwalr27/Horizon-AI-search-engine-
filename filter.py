import asyncio
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Set, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from logging_config import get_module_logger
from datetime import datetime, timedelta

class OptimizedFilter:
    def __init__(self, results: pd.DataFrame):
        self.filtered = results.copy()
        self.logger = get_module_logger("filter")
        self.blacklist_domains = self._load_blacklist()

    def _load_blacklist(self, blacklist_path="blacklist.txt") -> Set[str]:
        """Load blacklist with error handling."""
        try:
            with open(blacklist_path, "r") as f:
                return {domain.strip() for domain in f if domain.strip()}
        except Exception as e:
            self.logger.error(f"Blacklist loading error: {e}")
            return set()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc
        except Exception as e:
            self.logger.error(f"Error extracting domain from URL {url}: {e}")
            return ""

    def _basic_content_analysis(self, html: str) -> Dict[str, Any]:
        """Simplified content analysis with metadata extraction."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            
            # Extract metadata
            meta_date = None
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                if tag.get('property') in ['article:published_time', 'og:published_time'] or \
                   tag.get('name') in ['date', 'publish-date', 'article.published']:
                    meta_date = tag.get('content')
                    break
            
            return {
                "word_count": len(text.split()),
                "link_count": len(soup.find_all("a", href=True)),
                "published_date": meta_date,
                "has_date": bool(meta_date)
            }
        except Exception as e:
            self.logger.error(f"Content analysis error: {e}")
            return {
                "word_count": 0,
                "link_count": 0,
                "published_date": None,
                "has_date": False
            }

    def _calculate_time_relevance(self, date_str: str) -> float:
        """Calculate time-based relevance score."""
        try:
            if not date_str:
                return 0.5  # Default score for items without dates
                
            pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(pub_date.tzinfo)
            age = now - pub_date
            
            # Score based on age
            if age < timedelta(days=7):  # Within last week
                return 1.0
            elif age < timedelta(days=30):  # Within last month
                return 0.9
            elif age < timedelta(days=90):  # Within last 3 months
                return 0.8
            elif age < timedelta(days=365):  # Within last year
                return 0.7
            else:
                return 0.6
                
        except Exception as e:
            self.logger.error(f"Time relevance calculation error: {e}")
            return 0.5

    async def filter(self, min_words: int = 50, time_filter: str = None) -> pd.DataFrame:
    
        try:
        # Filter blacklisted domains
            domains = self.filtered["link"].apply(self._extract_domain)
            self.filtered = self.filtered[~domains.isin(self.blacklist_domains)].copy()

        # Apply time filter if specified
            if time_filter:
                now = datetime.utcnow()
                if time_filter == 'day':
                    cutoff = now - timedelta(days=1)
                elif time_filter == 'month':
                    cutoff = now - timedelta(days=30)
                elif time_filter == 'year':
                    cutoff = now - timedelta(days=365)
            
                self.filtered = self.filtered[
                    pd.to_datetime(self.filtered['created']) >= cutoff
                ].copy()

        # Parallel content analysis
            async def process_html(html):
                return self._basic_content_analysis(html)

            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                content_scores = await asyncio.gather(
                       *[loop.run_in_executor(executor, process_html, html) for html in self.filtered["html"]]
                )

        # Assign content scores
            self.filtered["content_score"] = [
                 score["word_count"] / max(1, score["link_count"]) for score in content_scores
             ]

        # Apply minimum word count filter
            self.filtered = self.filtered[self.filtered["content_score"] >= min_words].copy()

        # Update ranking
            if not self.filtered.empty:
                self.filtered["final_rank"] = range(1, len(self.filtered) + 1)

            return self.filtered

        except Exception as e:
            self.logger.error(f"Filtering error: {e}")
            return self.filtered
       
    def get_date_distribution(self) -> Dict[str, int]:
        """Get distribution of results by date periods."""
        try:
            dates = pd.to_datetime(self.filtered['published_date'], errors='coerce')
            now = datetime.now()
            
            return {
                'last_day': len(dates[dates >= now - timedelta(days=1)]),
                'last_week': len(dates[dates >= now - timedelta(weeks=1)]),
                'last_month': len(dates[dates >= now - timedelta(days=30)]),
                'last_year': len(dates[dates >= now - timedelta(days=365)]),
                'older': len(dates[dates < now - timedelta(days=365)]),
                'unknown': len(dates[dates.isna()])
            }
        except Exception as e:
            self.logger.error(f"Date distribution calculation error: {e}")
            return {
                'last_day': 0,
                'last_week': 0,
                'last_month': 0,
                'last_year': 0,
                'older': 0,
                'unknown': 0
            }