from pydantic_ai import Agent

from backend.core.config import get_settings
from backend.models.relationships import RelationshipExtractionResult, RelationshipType, RELATIONSHIP_TYPE_DESCRIPTIONS
from backend.models.entities import EntityResponse


class RelationshipExtractionAgent:
    def __init__(self, default_confidence_threshold: float = 0.6):
        self.default_confidence_threshold = default_confidence_threshold
        self.settings = get_settings()
        
        # Configure the agent with OpenAI model (uses env vars)
        self.agent = Agent(
            model=f"openai:{self.settings.default_model}",
            result_type=RelationshipExtractionResult,
            system_prompt=self._get_system_prompt(),
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for relationship extraction."""
        return f"""
You are an expert relationship extraction agent. Analyze entities and extract semantic relationships between them.

RELATIONSHIP TYPES:
{chr(10).join(f"- {rel_type.value}: {desc}" for rel_type, desc in RELATIONSHIP_TYPE_DESCRIPTIONS.items())}

GUIDELINES:
1. Extract relationships that are clearly supported by context
2. Assign confidence scores (0.0-1.0) based on certainty
3. Use specific relationship types when possible
4. Include relevant metadata

CONFIDENCE LEVELS:
- 0.9-1.0: Explicitly stated relationships
- 0.7-0.9: Clear contextual evidence
- 0.6-0.8: Reasonable with some context
- Below 0.6: Uncertain, use generic types

EXAMPLES:
- "John works for Microsoft" → WORKS_FOR (confidence: 0.95)
- "Microsoft is located in Seattle" → LOCATED_IN (confidence: 0.9)
- "YouTube competes with TikTok" → COMPETES_WITH (confidence: 0.85)

Focus on the most meaningful relationships with strong contextual support.
"""
    
    async def extract_relationships(self, entities: list[EntityResponse], context: str, relationship_types: list[RelationshipType] | None = None, confidence_threshold: float | None = None) -> RelationshipExtractionResult:
        """Extract relationships between entities using LLM for entity matching."""
        threshold = confidence_threshold or self.default_confidence_threshold
        
        # Create entity reference with IDs for LLM
        entity_refs = "\n".join([
            f"- ID: {entity.id} | Name: {entity.entity_name} | Type: {entity.entity_type.value} | Confidence: {entity.confidence:.2f}"
            for entity in entities
        ])
        
        prompt = f"""
CONTEXT: {context}

AVAILABLE ENTITIES:
{entity_refs}

Extract semantic relationships between these entities. Use the entity IDs (not names) in your response.
When you find a relationship, reference entities by their exact IDs from the list above.
Minimum confidence: {threshold}

IMPORTANT: Your response must use the exact entity IDs provided above.
"""
        
        if relationship_types:
            prompt += f"\nFocus on these relationship types: {', '.join(rt.value for rt in relationship_types)}"
        
        result = await self.agent.run(prompt)
        extraction_result = result.data
        
        # Validate that relationships use valid entity IDs
        valid_entity_ids = {entity.id for entity in entities}
        filtered_relationships = []
        
        for rel in extraction_result.relationships:
            if (rel.confidence >= threshold and 
                rel.source_entity_id in valid_entity_ids and 
                rel.target_entity_id in valid_entity_ids):
                filtered_relationships.append(rel)
        
        return RelationshipExtractionResult(
            relationships=filtered_relationships,
            total_relationships=len(filtered_relationships),
            relationship_types_found=list(set(rel.relationship_type for rel in filtered_relationships)),
            entities_processed=len(entities)
        )