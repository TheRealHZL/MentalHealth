"""
User Service - Main Service

Hauptservice für Benutzer-Management mit delegierten Subservices.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import date
import logging

from src.services.user.auth_service import AuthService
from src.services.user.profile_service import ProfileService
from src.services.user.registration_service import RegistrationService
from src.services.user.data_service import DataService
from src.services.user.therapist_service import TherapistService

logger = logging.getLogger(__name__)

class UserService:
    """Main User Service - Delegates to specialized services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize subservices
        self.auth = AuthService(db)
        self.profile = ProfileService(db)
        self.registration = RegistrationService(db)
        self.data = DataService(db)
        self.therapist = TherapistService(db)
    
    # =============================================================================
    # Registration Methods (Delegated)
    # =============================================================================
    
    async def create_patient(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        date_of_birth: Optional[date] = None,
        timezone: str = "Europe/Berlin"
    ):
        """Create new patient account"""
        return await self.registration.create_patient(
            email, password, first_name, last_name, date_of_birth, timezone
        )
    
    async def create_therapist(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        license_number: str,
        specializations: List[str],
        practice_address: Optional[str] = None,
        phone_number: Optional[str] = None,
        bio: Optional[str] = None,
        license_filename: Optional[str] = None
    ):
        """Create new therapist account"""
        return await self.registration.create_therapist(
            email, password, first_name, last_name, license_number,
            specializations, practice_address, phone_number, bio, license_filename
        )
    
    async def save_license_file(self, email: str, filename: str, content: bytes) -> str:
        """Save therapist license file"""
        return await self.registration.save_license_file(email, filename, content)
    
    # =============================================================================
    # Authentication Methods (Delegated)
    # =============================================================================
    
    async def get_user_by_id(self, user_id: str):
        """Get user by ID"""
        return await self.auth.get_user_by_id(user_id)
    
    async def get_user_by_email(self, email: str):
        """Get user by email"""
        return await self.auth.get_user_by_email(email)
    
    async def update_last_login(self, user_id: str) -> None:
        """Update last login timestamp"""
        return await self.auth.update_last_login(user_id)
    
    async def log_failed_login(self, user_id, email: str) -> None:
        """Log failed login attempt"""
        return await self.auth.log_failed_login(user_id, email)
    
    # =============================================================================
    # Profile Methods (Delegated)
    # =============================================================================
    
    async def update_user_profile(self, user_id: str, profile_data):
        """Update user profile"""
        return await self.profile.update_user_profile(user_id, profile_data)
    
    async def update_password(self, user_id: str, new_password: str) -> None:
        """Update user password"""
        return await self.profile.update_password(user_id, new_password)
    
    async def get_profile_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user profile statistics"""
        return await self.profile.get_profile_statistics(user_id)
    
    # =============================================================================
    # Therapist Methods (Delegated)
    # =============================================================================
    
    async def search_verified_therapists(
        self,
        location: Optional[str] = None,
        specialization: Optional[str] = None,
        radius: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for verified therapists"""
        return await self.therapist.search_verified_therapists(location, specialization, radius)
    
    async def notify_admin_for_verification(self, therapist_id) -> None:
        """Notify admin about new therapist registration"""
        return await self.therapist.notify_admin_for_verification(therapist_id)
    
    # =============================================================================
    # Data Management Methods (Delegated)
    # =============================================================================
    
    async def delete_user_account(self, user_id: str) -> Dict[str, Any]:
        """Delete user account and all data"""
        return await self.data.delete_user_account(user_id)
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for GDPR"""
        return await self.data.export_user_data(user_id)
    
    async def get_platform_statistics(self) -> Dict[str, Any]:
        """Get anonymized platform statistics"""
        return await self.data.get_platform_statistics()
