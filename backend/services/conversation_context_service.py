"""Lightweight conversation context service for conversational RAG."""

import re
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from backend.models.queries import QueryHistory


class ConversationContext(BaseModel):
    """Conversation context for query processing."""
    
    recent_queries: List[str] = Field(default_factory=list, description="Recent query texts")
    recent_responses: List[str] = Field(default_factory=list, description="Recent response texts")
    extracted_entities: List[str] = Field(default_factory=list, description="Entities from recent conversation")
    key_topics: List[str] = Field(default_factory=list, description="Key topics from recent conversation")
    session_duration: int = Field(default=0, description="Minutes since first query in session")
    context_summary: str = Field(default="", description="Brief summary of recent conversation")


class ConversationContextService:
    """Service for retrieving and processing conversation context."""
    
    def __init__(self, max_context_queries: int = 3, session_timeout_minutes: int = 30):
        self.max_context_queries = max_context_queries
        self.session_timeout_minutes = session_timeout_minutes
        
        # Simple entity/topic extraction patterns
        self.entity_patterns = [
            r'\b(travel|tourism|monetization|content|creator|influencer|brand|social media|platform|strategy|affiliate|course|coaching|YouTube|Instagram|TikTok|Facebook|Vietnamese|Vietnam)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns
        ]
        
        # Reference resolution patterns
        self.reference_patterns = {
            'they': r'\b(they|them|their|theirs)\b',
            'it': r'\b(it|its)\b',
            'this': r'\b(this|these|that|those)\b',
            'approach': r'\b(approach|strategy|method|technique|way)\b'
        }
    
    def extract_context_from_history(self, query_history: List[QueryHistory]) -> ConversationContext:
        """Extract conversation context from query history.
        
        Args:
            query_history: List of recent query history records
            
        Returns:
            ConversationContext with extracted information
        """
        if not query_history:
            return ConversationContext()
        
        # Filter to recent session (within timeout)
        recent_cutoff = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        recent_history = [
            q for q in query_history 
            if q.created_at >= recent_cutoff
        ][:self.max_context_queries]
        
        if not recent_history:
            return ConversationContext()
        
        # Extract basic information
        recent_queries = [q.query_text for q in recent_history]
        recent_responses = [q.response_text for q in recent_history]
        
        # Extract entities and topics
        all_text = " ".join(recent_queries + recent_responses)
        extracted_entities = self._extract_entities(all_text)
        key_topics = self._extract_key_topics(all_text)
        
        # Calculate session duration
        session_start = min(q.created_at for q in recent_history)
        session_duration = int((datetime.now() - session_start).total_seconds() / 60)
        
        # Create context summary
        context_summary = self._create_context_summary(recent_queries, extracted_entities, key_topics)
        
        return ConversationContext(
            recent_queries=recent_queries,
            recent_responses=recent_responses,
            extracted_entities=extracted_entities,
            key_topics=key_topics,
            session_duration=session_duration,
            context_summary=context_summary
        )
    
    def expand_query_with_context(self, current_query: str, context: ConversationContext) -> str:
        """Expand current query with conversation context.
        
        Args:
            current_query: Current user query
            context: Conversation context
            
        Returns:
            Expanded query with context
        """
        if not context.recent_queries:
            return current_query
        
        # Resolve references in current query
        expanded_query = self._resolve_references(current_query, context)
        
        # Add relevant context entities if query is short or has references
        if len(current_query.split()) < 5 or self._has_references(current_query):
            relevant_entities = self._get_relevant_entities(expanded_query, context)
            if relevant_entities:
                expanded_query += f" (context: {', '.join(relevant_entities)})"
        
        return expanded_query
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text using simple patterns."""
        entities = set()
        
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update(match.lower() if isinstance(match, str) else match for match in matches)
        
        # Filter out common words and very short entities
        filtered_entities = [
            entity for entity in entities 
            if len(entity) > 2 and entity not in {'the', 'and', 'for', 'are', 'can', 'has', 'had', 'not', 'use', 'may', 'new', 'get', 'see', 'way', 'now', 'own', 'say', 'she', 'may', 'use', 'her', 'all', 'any', 'can', 'had', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        ]
        
        return sorted(list(set(filtered_entities)))[:10]  # Limit to top 10
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        # Simple topic extraction based on frequent meaningful words
        topic_keywords = [
            'monetization', 'content', 'creator', 'travel', 'social media', 'strategy',
            'affiliate', 'marketing', 'youtube', 'instagram', 'platform', 'audience',
            'brand', 'influencer', 'coaching', 'course', 'vietnamese', 'trends'
        ]
        
        topics = []
        text_lower = text.lower()
        
        for topic in topic_keywords:
            if topic in text_lower:
                topics.append(topic)
        
        return topics[:5]  # Limit to top 5
    
    def _resolve_references(self, query: str, context: ConversationContext) -> str:
        """Resolve references in query using context."""
        if not context.recent_queries or not context.extracted_entities:
            return query
        
        resolved_query = query
        
        # Simple reference resolution
        if re.search(self.reference_patterns['they'], query, re.IGNORECASE):
            # Look for likely referents in recent entities
            likely_referents = [
                entity for entity in context.extracted_entities
                if entity in ['travel', 'creator', 'content', 'influencer', 'vietnamese']
            ]
            if likely_referents:
                # Replace with most likely referent
                resolved_query = re.sub(
                    self.reference_patterns['they'], 
                    f"{likely_referents[0]}s", 
                    resolved_query, 
                    flags=re.IGNORECASE
                )
        
        # Resolve "this approach" -> "monetization approach" etc.
        if re.search(self.reference_patterns['approach'], query, re.IGNORECASE):
            topic_context = [t for t in context.key_topics if t in ['monetization', 'marketing', 'content']]
            if topic_context:
                resolved_query = re.sub(
                    r'\bthis\s+(approach|strategy|method)\b',
                    f"{topic_context[0]} \\1",
                    resolved_query,
                    flags=re.IGNORECASE
                )
        
        return resolved_query
    
    def _has_references(self, query: str) -> bool:
        """Check if query contains references that need resolution."""
        for pattern in self.reference_patterns.values():
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _get_relevant_entities(self, query: str, context: ConversationContext) -> List[str]:
        """Get entities from context that are relevant to current query."""
        query_lower = query.lower()
        relevant_entities = []
        
        for entity in context.extracted_entities:
            # Include entity if it's related to query terms or is a key topic
            if (entity in query_lower or 
                any(topic in entity for topic in context.key_topics) or
                entity in ['travel', 'creator', 'content', 'vietnamese', 'monetization']):
                relevant_entities.append(entity)
        
        return relevant_entities[:3]  # Limit to top 3 most relevant
    
    def _create_context_summary(self, queries: List[str], entities: List[str], topics: List[str]) -> str:
        """Create a brief summary of conversation context."""
        if not queries:
            return ""
        
        # Create simple summary
        summary_parts = []
        
        if len(queries) > 1:
            summary_parts.append(f"Continuing discussion")
        
        if topics:
            summary_parts.append(f"about {', '.join(topics[:2])}")
        
        if entities:
            key_entities = [e for e in entities if e in ['travel', 'creator', 'vietnamese', 'content']]
            if key_entities:
                summary_parts.append(f"focusing on {', '.join(key_entities[:2])}")
        
        return " ".join(summary_parts) if summary_parts else "New conversation"


# Global service instance
conversation_context_service = ConversationContextService()