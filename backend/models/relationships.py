from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    # Core semantic relationships (KISS - only essential types)
    WORKS_FOR = "WORKS_FOR"
    LOCATED_IN = "LOCATED_IN"
    PART_OF = "PART_OF"
    OWNS = "OWNS"
    CREATES = "CREATES"
    USES = "USES"
    COMPETES_WITH = "COMPETES_WITH"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    INFLUENCES = "INFLUENCES"
    SIMILAR_TO = "SIMILAR_TO"
    RELATED_TO = "RELATED_TO"
    MENTIONED_WITH = "MENTIONED_WITH"


RELATIONSHIP_TYPE_DESCRIPTIONS = {
    RelationshipType.WORKS_FOR: "Employment or work relationship",
    RelationshipType.LOCATED_IN: "Geographic or spatial location",
    RelationshipType.PART_OF: "Component or element of larger entity",
    RelationshipType.OWNS: "Ownership or possession",
    RelationshipType.CREATES: "Creation or authorship",
    RelationshipType.USES: "Usage or utilization",
    RelationshipType.COMPETES_WITH: "Competition or rivalry",
    RelationshipType.COLLABORATES_WITH: "Collaboration or cooperation",
    RelationshipType.INFLUENCES: "Influence or effect on",
    RelationshipType.SIMILAR_TO: "Similarity or likeness",
    RelationshipType.RELATED_TO: "General relationship or connection",
    RelationshipType.MENTIONED_WITH: "Co-mentioned in content",
}


class RelationshipBase(BaseModel):
    relationship_type: RelationshipType = Field(..., description="The type of relationship")
    source_entity_id: UUID = Field(..., description="The ID of the source entity")
    target_entity_id: UUID = Field(..., description="The ID of the target entity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the relationship")
    weight: float = Field(1.0, ge=0.0, description="Weight for graph algorithms")
    metadata: dict | None = Field(None, description="Additional metadata about the relationship")


class RelationshipCreate(RelationshipBase):
    doc_id: UUID = Field(..., description="The ID of the document where relationship was found")


class RelationshipUpdate(BaseModel):
    relationship_type: RelationshipType | None = Field(None, description="Updated relationship type")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Updated confidence score")
    weight: float | None = Field(None, ge=0.0, description="Updated weight")
    metadata: dict | None = Field(None, description="Updated metadata")


class EntitySummary(BaseModel):
    id: UUID = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type")


class RelationshipResponse(RelationshipBase):
    id: UUID = Field(..., description="The unique identifier of the relationship")
    doc_id: UUID = Field(..., description="The ID of the document where relationship was found")
    created_at: datetime = Field(..., description="Timestamp when the relationship was created")
    source_entity: EntitySummary | None = Field(None, description="Source entity details")
    target_entity: EntitySummary | None = Field(None, description="Target entity details")

    class Config:
        from_attributes = True


class RelationshipList(BaseModel):
    relationships: list[RelationshipResponse]
    total: int = Field(..., ge=0, description="Total number of relationships")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of relationships per page")
    has_next: bool = Field(..., description="Whether there are more relationships available")


class RelationshipExtractionRequest(BaseModel):
    doc_id: UUID = Field(..., description="The ID of the document to extract relationships from")
    relationship_types: list[RelationshipType] | None = Field(None, description="Specific relationship types to extract")
    confidence_threshold: float | None = Field(0.6, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_relationships: int | None = Field(100, ge=1, le=1000, description="Maximum number of relationships to extract")
    force_reextract: bool | None = Field(False, description="Force re-extraction even if relationships exist")


class RelationshipExtractionStatus(BaseModel):
    doc_id: UUID = Field(..., description="The ID of the document being processed")
    status: str = Field(..., description="Current extraction status")
    relationships_extracted: int = Field(..., ge=0, description="Number of relationships extracted")
    relationship_types_found: list[RelationshipType] = Field(default_factory=list, description="Relationship types found")
    entities_processed: int = Field(..., ge=0, description="Number of entities processed")
    error_message: str | None = Field(None, description="Error message if extraction failed")
    started_at: datetime = Field(..., description="When extraction started")
    completed_at: datetime | None = Field(None, description="When extraction completed")


class RelationshipExtractionResult(BaseModel):
    relationships: list[RelationshipBase] = Field(..., description="List of extracted relationships with entity IDs")
    total_relationships: int = Field(..., ge=0, description="Total number of relationships extracted")
    relationship_types_found: list[RelationshipType] = Field(default_factory=list, description="Relationship types found")
    entities_processed: int = Field(..., ge=0, description="Number of entities processed")


class GraphPathResponse(BaseModel):
    source_entity_id: UUID = Field(..., description="Source entity ID")
    target_entity_id: UUID = Field(..., description="Target entity ID")
    path_found: bool = Field(..., description="Whether a path was found")
    path_length: int = Field(..., ge=0, description="Length of the path")
    path_cost: float = Field(..., ge=0.0, description="Total cost of the path")
    path_entities: list[UUID] = Field(default_factory=list, description="Entities in the path")
    path_relationships: list[UUID] = Field(default_factory=list, description="Relationships in the path")


class GraphStatsResponse(BaseModel):
    total_entities: int = Field(..., ge=0, description="Total number of entities")
    total_relationships: int = Field(..., ge=0, description="Total number of relationships")
    avg_relationships_per_entity: float = Field(..., ge=0.0, description="Average relationships per entity")
    most_connected_entity: UUID | None = Field(None, description="Most connected entity ID")
    relationship_type_distribution: dict[str, int] = Field(default_factory=dict, description="Distribution of relationship types")