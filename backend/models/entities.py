from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    # People & Roles
    PERSON = "PERSON"
    ROLE = "ROLE"
    PROFESSION = "PROFESSION"
    
    # Organizations & Structure
    ORGANIZATION = "ORGANIZATION"
    DEPARTMENT = "DEPARTMENT"
    BRAND = "BRAND"
    
    # Geography & Location
    LOCATION = "LOCATION"
    COUNTRY = "COUNTRY"
    CITY = "CITY"
    REGION = "REGION"
    
    # Time & Events
    DATE = "DATE"
    TIME_PERIOD = "TIME_PERIOD"
    EVENT = "EVENT"
    ERA = "ERA"
    
    # Content & Knowledge
    CONCEPT = "CONCEPT"
    TOPIC = "TOPIC"
    KEYWORD = "KEYWORD"
    CATEGORY = "CATEGORY"
    METHODOLOGY = "METHODOLOGY"
    THEORY = "THEORY"
    
    # Activities & Processes
    ACTION = "ACTION"
    PROCESS = "PROCESS"
    PROJECT = "PROJECT"
    PROCEDURE = "PROCEDURE"
    
    # Technology & Tools
    TECHNOLOGY = "TECHNOLOGY"
    TOOL = "TOOL"
    SOFTWARE = "SOFTWARE"
    PLATFORM = "PLATFORM"
    
    # Products & Services
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    FEATURE = "FEATURE"
    
    # Business & Finance
    CURRENCY = "CURRENCY"
    METRIC = "METRIC"
    KPI = "KPI"
    INDUSTRY = "INDUSTRY"
    MARKET = "MARKET"
    
    # Communication & Media
    DOCUMENT = "DOCUMENT"
    MEDIA = "MEDIA"
    COMMUNICATION = "COMMUNICATION"
    
    # Legal & Compliance
    REGULATION = "REGULATION"
    LAW = "LAW"
    POLICY = "POLICY"
    REQUIREMENT = "REQUIREMENT"
    
    # Qualitative & Abstract
    SENTIMENT = "SENTIMENT"
    QUALITY = "QUALITY"
    RELATIONSHIP = "RELATIONSHIP"
    BENEFIT = "BENEFIT"
    CHALLENGE = "CHALLENGE"
    OPPORTUNITY = "OPPORTUNITY"
    RISK = "RISK"
    
    # Research & Analysis
    FINDING = "FINDING"
    INSIGHT = "INSIGHT"
    HYPOTHESIS = "HYPOTHESIS"
    DATA_SOURCE = "DATA_SOURCE"
    
    # Other
    MISC = "MISC"


ENTITY_TYPE_DESCRIPTIONS = {
    # People & Roles
    EntityType.PERSON: "Individual people, names, personalities",
    EntityType.ROLE: "Job titles, positions, responsibilities", 
    EntityType.PROFESSION: "Careers, occupations, specializations",
    
    # Organizations & Structure
    EntityType.ORGANIZATION: "Companies, institutions, groups, teams",
    EntityType.DEPARTMENT: "Divisions, departments, organizational units",
    EntityType.BRAND: "Product brands, company brands, trademarks",
    
    # Geography & Location
    EntityType.LOCATION: "Places, addresses, geographical entities",
    EntityType.COUNTRY: "Specific countries and nations",
    EntityType.CITY: "Cities, towns, municipalities",
    EntityType.REGION: "States, provinces, regions, areas",
    
    # Time & Events
    EntityType.DATE: "Specific dates, timestamps, deadlines",
    EntityType.TIME_PERIOD: "Durations, time ranges, schedules",
    EntityType.EVENT: "Events, meetings, occurrences, milestones",
    EntityType.ERA: "Historical periods, epochs, generations",
    
    # Content & Knowledge
    EntityType.CONCEPT: "Abstract concepts, ideas, themes",
    EntityType.TOPIC: "Subject matters, discussion topics",
    EntityType.KEYWORD: "Important terms, search terms, tags",
    EntityType.CATEGORY: "Classifications, types, groups",
    EntityType.METHODOLOGY: "Methods, approaches, frameworks",
    EntityType.THEORY: "Theoretical concepts, models, principles",
    
    # Activities & Processes
    EntityType.ACTION: "Activities, tasks, actions taken",
    EntityType.PROCESS: "Business processes, workflows, procedures",
    EntityType.PROJECT: "Specific projects, initiatives, programs",
    EntityType.PROCEDURE: "Step-by-step procedures, protocols",
    
    # Technology & Tools
    EntityType.TECHNOLOGY: "Technologies, technical concepts, systems",
    EntityType.TOOL: "Tools, instruments, applications, utilities",
    EntityType.SOFTWARE: "Software applications, programs, systems",
    EntityType.PLATFORM: "Platforms, environments, infrastructures",
    
    # Products & Services
    EntityType.PRODUCT: "Products, offerings, solutions",
    EntityType.SERVICE: "Services, support, assistance",
    EntityType.FEATURE: "Product features, capabilities, functions",
    
    # Business & Finance
    EntityType.CURRENCY: "Money, financial amounts, costs",
    EntityType.METRIC: "Measurements, statistics, numbers",
    EntityType.KPI: "Key performance indicators, goals, targets",
    EntityType.INDUSTRY: "Business sectors, industries, markets",
    EntityType.MARKET: "Market segments, customer groups, audiences",
    
    # Communication & Media
    EntityType.DOCUMENT: "Reports, papers, files, documentation",
    EntityType.MEDIA: "Publications, channels, platforms, content",
    EntityType.COMMUNICATION: "Communications, messages, interactions",
    
    # Legal & Compliance
    EntityType.REGULATION: "Regulations, rules, standards",
    EntityType.LAW: "Laws, legal requirements, statutes",
    EntityType.POLICY: "Policies, guidelines, principles",
    EntityType.REQUIREMENT: "Requirements, specifications, criteria",
    
    # Qualitative & Abstract
    EntityType.SENTIMENT: "Emotions, feelings, attitudes, opinions",
    EntityType.QUALITY: "Characteristics, attributes, properties",
    EntityType.RELATIONSHIP: "Connections, associations, relationships",
    EntityType.BENEFIT: "Benefits, advantages, positive outcomes",
    EntityType.CHALLENGE: "Challenges, problems, obstacles",
    EntityType.OPPORTUNITY: "Opportunities, possibilities, potential",
    EntityType.RISK: "Risks, threats, concerns, issues",
    
    # Research & Analysis
    EntityType.FINDING: "Research findings, discoveries, results",
    EntityType.INSIGHT: "Insights, observations, learnings",
    EntityType.HYPOTHESIS: "Hypotheses, assumptions, theories",
    EntityType.DATA_SOURCE: "Data sources, datasets, references",
    
    # Other
    EntityType.MISC: "Miscellaneous entities not fitting other categories"
}


class EntityBase(BaseModel):
    entity_type: EntityType = Field(..., description="The type of entity")
    entity_name: str = Field(..., min_length=1, max_length=255, description="The name of the entity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the extraction")
    metadata: dict | None = Field(None, description="Additional metadata about the entity")


class EntityCreate(EntityBase):
    chunk_id: UUID = Field(..., description="The ID of the chunk this entity belongs to")


class EntityUpdate(BaseModel):
    entity_name: str | None = Field(None, min_length=1, max_length=255, description="Updated entity name")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Updated confidence score")
    metadata: dict | None = Field(None, description="Updated metadata")


class EntityResponse(EntityBase):
    id: UUID = Field(..., description="The unique identifier of the entity")
    chunk_id: UUID = Field(..., description="The ID of the chunk this entity belongs to")
    created_at: datetime = Field(..., description="Timestamp when the entity was created")

    class Config:
        from_attributes = True


class EntityList(BaseModel):
    entities: list[EntityResponse]
    total: int = Field(..., ge=0, description="Total number of entities")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of entities per page")
    has_next: bool = Field(..., description="Whether there are more entities available")


class EntityExtractionRequest(BaseModel):
    chunk_id: UUID = Field(..., description="The ID of the chunk to extract entities from")
    entity_types: list[EntityType] | None = Field(None, description="Specific entity types to extract")
    confidence_threshold: float | None = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    force_reextract: bool | None = Field(False, description="Force re-extraction even if entities exist")


class EntityExtractionStatus(BaseModel):
    chunk_id: UUID = Field(..., description="The ID of the chunk being processed")
    status: str = Field(..., description="Current extraction status")
    entities_extracted: int = Field(..., ge=0, description="Number of entities extracted")
    entity_types_found: list[EntityType] = Field(default_factory=list, description="Entity types found")
    error_message: str | None = Field(None, description="Error message if extraction failed")
    started_at: datetime = Field(..., description="When extraction started")
    completed_at: datetime | None = Field(None, description="When extraction completed")


class EntityExtractionResult(BaseModel):
    entities: list[EntityBase] = Field(..., description="List of extracted entities")
    total_entities: int = Field(..., ge=0, description="Total number of entities extracted")
    entity_types_found: list[EntityType] = Field(default_factory=list, description="Entity types found")