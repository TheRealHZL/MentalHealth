"""
User & Authentication Schemas

Pydantic Schemas für User-Management und Authentication.
"""

import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """User role enumeration"""

    PATIENT = "patient"
    THERAPIST = "therapist"
    ADMIN = "admin"


class UserRegistration(BaseModel):
    """User registration schema"""

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password (8-128 characters)"
    )
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    timezone: Optional[str] = Field("Europe/Berlin", description="User timezone")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class TherapistRegistration(BaseModel):
    """Therapist registration schema"""

    email: EmailStr = Field(..., description="Professional email address")
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(
        ..., min_length=3, max_length=100, description="Professional license number"
    )
    specializations: List[str] = Field(..., description="Areas of specialization")
    practice_address: Optional[str] = Field(
        None, max_length=500, description="Practice address"
    )
    phone_number: Optional[str] = Field(None, description="Practice phone number")
    bio: Optional[str] = Field(None, max_length=2000, description="Professional bio")


class TherapistVerification(BaseModel):
    """Therapist verification schema"""

    therapist_id: str = Field(..., description="Therapist ID to verify")
    admin_notes: Optional[str] = Field(
        None, max_length=1000, description="Admin verification notes"
    )


class UserLogin(BaseModel):
    """User login schema"""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class PasswordChange(BaseModel):
    """Password change schema"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )


class UserProfileUpdate(BaseModel):
    """User profile update schema"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    timezone: Optional[str] = Field(None, description="User timezone")
    bio: Optional[str] = Field(None, max_length=2000)
    specializations: Optional[List[str]] = None
    practice_address: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response schema"""

    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_verified: bool
    timezone: str
    created_at: datetime
    last_login: Optional[datetime] = None
    statistics: Optional[Dict[str, Any]] = None

    # Therapist-specific fields
    license_number: Optional[str] = None
    specializations: Optional[List[str]] = None
    practice_address: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    verification_status: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    message: Optional[str] = None
    next_steps: Optional[List[str]] = None
