"""
models.py
Pydantic response models for all 16 features + marketing engine.
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel


# ─── Shared primitives ────────────────────────────────────────────────────────

class FitnessProfile(BaseModel):
    office_lunch:      float | None = None
    repeat_habit:      float | None = None
    social_dwell:      float | None = None
    group_energy:      float | None = None
    destination_visit: float | None = None
    operational_quality:    float | None = None
    retention_strength:     float | None = None
    monetization_potential: float | None = None


class VenueBase(BaseModel):
    id:       int
    place_id: str
    name:     str
    area:     str | None = None
    city:     str | None = None
    types:    list[str] = []
    lat:      float | None = None
    lng:      float | None = None
    locality: str | None = None
    fitness:  FitnessProfile | None = None
    fitness_vector: list[float] | None = None


# ─── Feature 1: Similar Venues ────────────────────────────────────────────────

class SimilarVenueEntry(BaseModel):
    rank:                 int
    similarity_score:     float
    shared_primitive_count: int
    shared_primitives:    list[str] = []
    venue:                VenueBase


class SimilarVenuesResponse(BaseModel):
    venue:          VenueBase
    similar_venues: list[SimilarVenueEntry]
    total_found:    int


# ─── Feature 2: Consulting Redirect ───────────────────────────────────────────

class GapAnalysis(BaseModel):
    target_fitness:    str
    current_score:     float | None = None
    benchmark_score:   float | None = None
    gap:               float | None = None
    top_interventions: list[dict[str, Any]] = []


class ConsultingReferenceVenue(BaseModel):
    rank:                  int
    venue:                 VenueBase
    target_fitness_score:  float | None = None
    similarity_score:      float | None = None
    shared_primitives:     list[str] = []


class ConsultingRedirectResponse(BaseModel):
    your_venue:       VenueBase
    target_fitness:   str
    gap_analysis:     GapAnalysis
    reference_venues: list[ConsultingReferenceVenue]


# ─── Marketing Engine ─────────────────────────────────────────────────────────

class ChannelRecommendation(BaseModel):
    channel:           str
    effectiveness:     int
    roi_lift_min:      float | None = None
    roi_lift_max:      float | None = None
    primary_use_case:  str | None = None
    research_confidence: str | None = None


class CampaignTemplate(BaseModel):
    id:                     int
    demographic_segment:    str | None = None
    target_archetype:       str | None = None
    channel:                str | None = None
    message_template:       str | None = None
    suggested_roi_lift_pct: float | None = None
    confidence_level:       str | None = None
    implementation_guide:   str | None = None


class MechanismRecommendation(BaseModel):
    rank:               int
    fitness_alignment:  str
    alignment_score:    float
    mechanism_id:       str
    name:               str
    description:        str | None = None
    key_triggers:       list[str] = []
    timeline:           str | None = None
    top_channels:       list[ChannelRecommendation] = []
    campaign_templates: list[CampaignTemplate] = []


class MarketingRecommendationsResponse(BaseModel):
    venue:                   VenueBase
    fitness_profile:         FitnessProfile
    recommended_mechanisms:  list[MechanismRecommendation]
    confidence_note:         str = (
        'Recommendations derived from venue fitness profile and '
        'India-specific behavioral research (Phase 1). '
        'Validate with Module 3 field measurements.'
    )


# ─── Health ───────────────────────────────────────────────────────────────────

class TableCount(BaseModel):
    table:  str
    rows:   int


class HealthResponse(BaseModel):
    status:       str
    db_connected: bool
    table_counts: list[TableCount] = []
    version:      str = '1.0.0'
