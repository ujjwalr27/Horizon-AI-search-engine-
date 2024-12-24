import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Optional
from logging_config import get_module_logger

class SimplifiedMLRanker:
    def __init__(self):
        self.logger = get_module_logger('ml_ranking')
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            dtype=np.float32,
            norm='l2',
            smooth_idf=True
        )
        self.scaler = MinMaxScaler()
        
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for ranking."""
        try:
            return str(text).lower().strip()
        except Exception as e:
            self.logger.error(f"Text preprocessing error: {e}")
            return ""

    def _combine_features(self, df: pd.DataFrame) -> List[str]:
        """Combine text features for ranking."""
        try:
            features = []
            for _, row in df.iterrows():
                text = f"{row.get('title', '')} {row.get('snippet', '')}"
                features.append(self._preprocess_text(text))
            return features
        except Exception as e:
            self.logger.error(f"Feature combination error: {e}")
            return [""] * len(df)

    def predict_ranking(self, results: pd.DataFrame) -> pd.DataFrame:
        """Predict ranking scores with error handling and validation."""
        try:
            if results.empty:
                return results

            # Validate required columns
            required_columns = ['title', 'snippet']
            if not all(col in results.columns for col in required_columns):
                self.logger.error("Missing required columns")
                results['ml_rank'] = 1.0
                return results

            # Combine and process features
            text_features = self._combine_features(results)
            
            # Calculate TF-IDF scores
            tfidf_matrix = self.vectorizer.fit_transform(text_features)
            
            # Calculate document importance scores
            importance_scores = np.asarray(tfidf_matrix.sum(axis=1)).flatten()
            
            # Scale scores to [0, 1] range
            if len(importance_scores) > 1:
                importance_scores = self.scaler.fit_transform(
                    importance_scores.reshape(-1, 1)
                ).flatten()
            
            # Add scores to results
            results['ml_rank'] = importance_scores
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ranking error: {e}")
            # Fallback to default ranking
            results['ml_rank'] = 1.0
            return results

    def get_feature_importance(self, results: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Get feature importance scores for debugging."""
        try:
            if results.empty:
                return None

            text_features = self._combine_features(results)
            self.vectorizer.fit_transform(text_features)
            
            feature_scores = dict(zip(
                self.vectorizer.get_feature_names_out(),
                self.vectorizer.idf_
            ))
            
            return {k: v for k, v in sorted(
                feature_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]}
            
        except Exception as e:
            self.logger.error(f"Feature importance calculation error: {e}")
            return None