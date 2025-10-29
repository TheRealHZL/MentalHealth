"""
Export Schemas

Pydantic Schemas für Data Export (GDPR compliance).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date


class DataExportRequest(BaseModel):
    """Data export request schema"""
    include_mood_entries: bool = Field(True, description="Include mood entries")
    include_dream_entries: bool = Field(True, description="Include dream entries")
    include_therapy_notes: bool = Field(True, description="Include therapy notes")
    include_sharing_data: bool = Field(True, description="Include sharing data")
    include_ai_data: bool = Field(True, description="Include AI-generated data")
    date_range_start: Optional[date] = Field(None, description="Export data from this date")
    date_range_end: Optional[date] = Field(None, description="Export data until this date")
    format: str = Field("json", pattern="^(json|csv)$", description="Export format")


class DataExportResponse(BaseModel):
    """Data export response schema"""
    export_id: str
    generated_at: datetime
    user_id: str
    export_type: str
    data_format: str
    gdpr_compliant: bool
    user_profile: Dict[str, Any]
    content_data: Dict[str, Any]
    sharing_data: Dict[str, Any]
    activity_data: Dict[str, Any]
    data_summary: Dict[str, Any]
    legal_information: Dict[str, Any]
