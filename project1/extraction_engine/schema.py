"""
Pydantic models for knowledge extraction JSON schema.
Enforces Shatalov constraints and validates extraction output.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class SourceSpan(BaseModel):
    """Character position in source text."""
    start_char: int
    end_char: int


class Relation(BaseModel):
    """Single relationship between concepts/units."""
    rel: str
    from_: str = Field(alias="from")
    to: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class Seeds(BaseModel):
    """Minimal information to reconstruct understanding."""
    rule_or_core: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    example: Optional[str] = None
    mistake_and_fix: Optional[str] = None


class MeaningUnit(BaseModel):
    """Atomic unit of educational content."""
    unit_id: str
    type: Literal[
        "definition",
        "claim_theorem",
        "method_procedure",
        "example",
        "consequence",
        "warning_common_mistake",
        "background"
    ]
    source_span: SourceSpan
    summary: str
    key_terms: List[str]
    symbols: List[str] = Field(default_factory=list)
    concept_refs: List[str] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    seeds: Seeds


class Concept(BaseModel):
    """Extracted concept with metadata."""
    concept_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    short_def: Optional[str] = None
    tags: List[Literal["concept", "method", "theorem", "notation", "pitfall"]]
    prerequisites: List[str] = Field(default_factory=list)
    contrasts: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class RelationGraph(BaseModel):
    """Global relationship in knowledge graph."""
    rel_id: str
    type: Literal[
        "prerequisite",
        "contrasts_with",
        "used_for",
        "example_of",
        "counterexample_of",
        "causes",
        "part_of",
        "is_a",
        "defines"
    ]
    from_: str = Field(alias="from")
    to: str
    label: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class MiniLink(BaseModel):
    """Compact link for skeleton card visualization."""
    from_: str = Field(alias="from")
    rel: str
    to: str
    label: str


class SeedPack(BaseModel):
    """Reconstruction seeds for a block."""
    rule_plus_conditions: Optional[str] = None
    procedure_steps: List[str] = Field(default_factory=list)
    one_strong_example: Optional[str] = None
    one_common_mistake: Optional[str] = None


class Block(BaseModel):
    """Single block in Shatalov skeleton card."""
    block_id: str
    title: str
    anchors: List[str] = Field(min_length=1, max_length=3)
    unit_refs: List[str] = Field(default_factory=list)
    concept_refs: List[str] = Field(default_factory=list)
    mini_links: List[MiniLink] = Field(default_factory=list)
    seed_pack: SeedPack

    @field_validator('anchors')
    @classmethod
    def validate_anchors(cls, v):
        """Ensure anchors are short (2-5 words)."""
        for anchor in v:
            word_count = len(anchor.split())
            if word_count > 5:
                raise ValueError(f"Anchor '{anchor}' too long ({word_count} words, max 5)")
        return v


class SkeletonCard(BaseModel):
    """Shatalov-style skeleton card for a topic."""
    card_id: str
    topic: str
    blocks: List[Block] = Field(min_length=1, max_length=7)

    @field_validator('blocks')
    @classmethod
    def validate_blocks(cls, v):
        """Enforce Shatalov constraint: 5-7 blocks per card."""
        if not (5 <= len(v) <= 7):
            raise ValueError(f"Skeleton card must have 5-7 blocks, got {len(v)}")
        return v


class CoverageEstimate(BaseModel):
    """Estimated coverage of extracted knowledge."""
    major_concepts: int
    major_methods: int
    major_mistakes: int


class QualityChecks(BaseModel):
    """Validation and quality metrics."""
    shatalov_constraint_ok: bool
    num_blocks_per_card: List[int]
    missing_prereqs_warnings: List[str]
    knowledge_islands: List[str]
    top_contrasts: List[str]
    coverage_estimate: CoverageEstimate


class Meta(BaseModel):
    """Metadata about the extraction."""
    course_title: Optional[str] = None
    chapter_title: Optional[str] = None
    domain: str
    language: str
    compression_notes: str


class ExtractionOutput(BaseModel):
    """Complete extraction output schema."""
    meta: Meta
    meaning_units: List[MeaningUnit]
    concepts: List[Concept]
    relations_graph: List[RelationGraph]
    skeleton_cards: List[SkeletonCard]
    quality_checks: QualityChecks
