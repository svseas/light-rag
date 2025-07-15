from pydantic_ai import Agent

from backend.core.config import get_settings
from backend.models.entities import EntityExtractionResult, EntityType, ENTITY_TYPE_DESCRIPTIONS


class EntityExtractionAgent:
    def __init__(self, default_confidence_threshold: float = 0.5):
        self.default_confidence_threshold = default_confidence_threshold
        self.settings = get_settings()
        
        # Configure the agent with OpenAI model (uses env vars)
        self.agent = Agent(
            model=f"openai:{self.settings.default_model}",
            result_type=EntityExtractionResult,
            system_prompt=self._get_system_prompt(),
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for entity extraction."""
        return f"""
You are an expert entity extraction agent. Your task is to extract structured entities from text chunks.

ENTITY TYPES AND DESCRIPTIONS:
{chr(10).join(f"- {entity_type.value}: {desc}" for entity_type, desc in ENTITY_TYPE_DESCRIPTIONS.items())}

EXTRACTION GUIDELINES:
1. Extract entities that are clearly mentioned or referenced in the text
2. Assign appropriate entity types based on context and meaning
3. Provide confidence scores (0.0-1.0) based on certainty of classification
4. Use entity_name as the exact text mention when possible
5. Prefer specific entity types over generic ones (e.g., CITY over LOCATION)
6. Include context-relevant metadata when helpful

CONFIDENCE SCORING:
- 0.9-1.0: Very clear, unambiguous entities
- 0.7-0.9: Clear entities with good context
- 0.5-0.7: Reasonable entities with some ambiguity
- 0.3-0.5: Uncertain entities, might need review
- 0.0-0.3: Very uncertain, low confidence

EXTRACTION EXAMPLES:
- "Microsoft Corporation" → ORGANIZATION (confidence: 0.95)
- "CEO" → ROLE (confidence: 0.9)
- "San Francisco" → CITY (confidence: 0.9)
- "artificial intelligence" → TECHNOLOGY (confidence: 0.8)
- "Q4 2024" → DATE (confidence: 0.85)
- "revenue growth" → METRIC (confidence: 0.8)
- "market opportunity" → OPPORTUNITY (confidence: 0.75)

Focus on extracting the most relevant and important entities. Avoid over-extraction of common words.
Return entities with their types, confidence scores, and relevant metadata.
"""
    
    async def extract_entities(self, text: str, entity_types: list[EntityType] | None = None, confidence_threshold: float | None = None) -> EntityExtractionResult:
        """Extract entities from text using the PydanticAI agent.
        
        Args:
            text: The text to extract entities from
            entity_types: Optional list of specific entity types to extract
            confidence_threshold: Minimum confidence threshold for entities
            
        Returns:
            EntityExtractionResult with extracted entities
        """
        threshold = confidence_threshold or self.default_confidence_threshold
        
        prompt = f"Extract entities from this text:\n\n{text}\n\n"
        
        if entity_types:
            prompt += f"Focus on these entity types: {', '.join(et.value for et in entity_types)}\n"
        
        prompt += f"Minimum confidence threshold: {threshold}\n"
        prompt += "Return structured entities with types, names, confidence scores, and metadata."
        
        result = await self.agent.run(
            prompt,
            model=self.settings.default_model,
        )
        
        # Extract the result data
        extraction_result = result.data
        
        # Filter by confidence threshold
        filtered_entities = [
            entity for entity in extraction_result.entities 
            if entity.confidence >= threshold
        ]
        
        return EntityExtractionResult(
            entities=filtered_entities,
            total_entities=len(filtered_entities),
            entity_types_found=list(set(entity.entity_type for entity in filtered_entities))
        )