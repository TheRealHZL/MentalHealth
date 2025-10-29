"""
Sharing Schemas

Pydantic Schemas für Data Sharing zwischen Patienten und Therapeuten.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SharePermission(str, Enum):
    """Share permission levels"""
    READ_ONLY = "read_only"
    READ_COMMENT = "read_comment"
    COLLABORATIVE = "collaborative"


class ShareKeyCreate(BaseModel):
    """Create share key schema"""
    therapist_email: EmailStr = Field(..., description="Therapist email address")
    permission_level: SharePermission = Field(SharePermission.READ_ONLY, description="Permission level")
    include_mood_entries: bool = Field(True, description="Include mood entries?")
    include_dream_entries: bool = Field(False, description="Include dream entries?")
    include_therapy_notes: bool = Field(True, description="Include therapy notes?")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    max_sessions: Optional[int] = Field(None, ge=1, le=1000, description="Maximum sessions")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes about sharing")
    
    # Advanced options
    date_range_start: Optional[datetime] = Field(None, description="Only share data after this date")
    date_range_end: Optional[datetime] = Field(None, description="Only share data before this date")
    exclude_tags: Optional[List[str]] = None
    emergency_contact: bool = Field(False, description="Is this therapist an emergency contact?")
    crisis_access: bool = Field(False, description="Can access during crisis situations?")


class TherapistAccessRequest(BaseModel):
    """Therapist access request schema"""
    share_key: str = Field(..., min_length=10, description="Share key from patient")
    message: Optional[str] = Field(None, max_length=500, description="Message to patient")


class ShareKeyResponse(BaseModel):
    """Share key response schema"""
    id: str
    share_key: str
    therapist_email: str
    permission_level: SharePermission
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    max_sessions: Optional[int] = None
    access_count: int
    last_accessed: Optional[datetime] = None
    data_permissions: Dict[str, bool]
    limits: Dict[str, Any]
    instructions: Dict[str, List[str]]


class PatientOverview(BaseModel):
    """Patient overview for therapists"""
    patient_id: str
    patient_name: str
    permission_level: str
    shared_since: datetime
    last_accessed: Optional[datetime] = None
    access_count: int
    data_access: Dict[str, bool]
    summary_stats: Dict[str, Any]
    expires_at: Optional[datetime] = None
