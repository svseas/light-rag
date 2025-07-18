"""Document freshness scoring utilities for search results."""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FreshnessConfig(BaseModel):
    """Configuration for freshness scoring."""
    
    # Decay parameters
    half_life_days: int = Field(default=30, description="Days for freshness to decay to 50%")
    max_age_days: int = Field(default=365, description="Maximum age before score approaches 0")
    
    # Scoring weights
    base_weight: float = Field(default=0.2, description="Base weight for freshness in final score")
    temporal_queries_weight: float = Field(default=0.4, description="Weight for temporal queries")
    
    # Thresholds
    recent_threshold_days: int = Field(default=7, description="Days to consider 'recent'")
    old_threshold_days: int = Field(default=180, description="Days to consider 'old'")


class FreshnessScore(BaseModel):
    """Individual freshness score result."""
    
    document_id: str = Field(..., description="Document identifier")
    created_at: datetime = Field(..., description="Document creation timestamp")
    age_days: int = Field(..., description="Age in days")
    freshness_score: float = Field(..., description="Freshness score (0-1)")
    freshness_category: str = Field(..., description="recent, moderate, old, very_old")
    boost_factor: float = Field(..., description="Multiplier for final score")


class FreshnessScorer:
    """Utility class for calculating document freshness scores."""
    
    def __init__(self, config: FreshnessConfig = None):
        self.config = config or FreshnessConfig()
    
    def calculate_freshness_score(self, created_at: datetime, 
                                 current_time: datetime = None) -> FreshnessScore:
        """Calculate freshness score for a document.
        
        Args:
            created_at: Document creation timestamp
            current_time: Current time (defaults to now)
            
        Returns:
            FreshnessScore with calculated metrics
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Ensure both datetimes are timezone-aware
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        # Calculate age in days
        age_timedelta = current_time - created_at
        age_days = age_timedelta.days
        
        # Calculate exponential decay score
        # Formula: score = exp(-ln(2) * age_days / half_life_days)
        # This gives 50% score at half_life_days
        decay_factor = math.log(2) / self.config.half_life_days
        freshness_score = math.exp(-decay_factor * age_days)
        
        # Clamp to minimum based on max_age_days
        min_score = math.exp(-decay_factor * self.config.max_age_days)
        freshness_score = max(freshness_score, min_score)
        
        # Determine freshness category
        if age_days <= self.config.recent_threshold_days:
            category = "recent"
            boost_factor = 1.0 + (self.config.base_weight * 0.5)
        elif age_days <= self.config.old_threshold_days:
            category = "moderate"
            boost_factor = 1.0
        elif age_days <= self.config.max_age_days:
            category = "old"
            boost_factor = 1.0 - (self.config.base_weight * 0.3)
        else:
            category = "very_old"
            boost_factor = 1.0 - (self.config.base_weight * 0.5)
        
        # Ensure boost factor is positive
        boost_factor = max(boost_factor, 0.1)
        
        return FreshnessScore(
            document_id=str(created_at),  # Placeholder, should be actual doc ID
            created_at=created_at,
            age_days=age_days,
            freshness_score=freshness_score,
            freshness_category=category,
            boost_factor=boost_factor
        )
    
    def is_temporal_query(self, query: str) -> bool:
        """Determine if query has temporal intent.
        
        Args:
            query: User query text
            
        Returns:
            True if query appears to be temporal
        """
        temporal_keywords = [
            "recent", "latest", "new", "current", "today", "yesterday",
            "last week", "last month", "this year", "2024", "2023",
            "updated", "fresh", "modern", "contemporary", "now",
            "recently", "currently", "ongoing", "latest news"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in temporal_keywords)
    
    def calculate_weight_for_query(self, query: str) -> float:
        """Calculate freshness weight based on query type.
        
        Args:
            query: User query text
            
        Returns:
            Weight multiplier for freshness scoring
        """
        if self.is_temporal_query(query):
            return self.config.temporal_queries_weight
        else:
            return self.config.base_weight
    
    def apply_freshness_boost(self, original_score: float, 
                             freshness_score: FreshnessScore,
                             query: str) -> float:
        """Apply freshness boost to original search score.
        
        Args:
            original_score: Original relevance score
            freshness_score: Calculated freshness score
            query: User query (for temporal detection)
            
        Returns:
            Boosted score incorporating freshness
        """
        weight = self.calculate_weight_for_query(query)
        
        # Calculate final score: original * (1 + weight * freshness_boost)
        # This preserves original ranking while boosting fresh content
        freshness_boost = (freshness_score.boost_factor - 1.0) * weight
        final_score = original_score * (1.0 + freshness_boost)
        
        return final_score
    
    def get_freshness_explanation(self, freshness_score: FreshnessScore) -> str:
        """Get human-readable explanation of freshness score.
        
        Args:
            freshness_score: Calculated freshness score
            
        Returns:
            Human-readable explanation
        """
        age_str = f"{freshness_score.age_days} days old"
        
        if freshness_score.freshness_category == "recent":
            return f"Recent content ({age_str}) - boosted in ranking"
        elif freshness_score.freshness_category == "moderate":
            return f"Moderately fresh content ({age_str}) - neutral ranking"
        elif freshness_score.freshness_category == "old":
            return f"Older content ({age_str}) - slightly reduced ranking"
        else:
            return f"Very old content ({age_str}) - reduced ranking"


# Global scorer instance
default_freshness_scorer = FreshnessScorer()