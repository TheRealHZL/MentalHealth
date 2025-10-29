"""
Email Service - User Communications

Sendet Willkommens-Emails und Benachrichtigungen.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Email Service für User-Kommunikation"""
    
    def __init__(self):
        self.sender_email = "noreply@mindbridge.com"
        self.sender_name = "MindBridge Team"
    
    async def send_welcome_email(
        self, 
        to_email: str, 
        first_name: str, 
        has_therapist: bool = False
    ) -> bool:
        """Send welcome email (alias for send_patient_welcome_email)"""
        return await self.send_patient_welcome_email(to_email, first_name, has_therapist)
    
    async def send_patient_welcome_email(
        self, 
        email: str, 
        first_name: str, 
        has_therapist: bool = False
    ) -> bool:
        """Send welcome email to patients"""
        try:
            subject = f"Willkommen bei MindBridge, {first_name}! 🌟"
            
            if has_therapist:
                content = self._get_patient_with_therapist_template(first_name)
            else:
                content = self._get_self_help_patient_template(first_name)
            
            # TODO: Implement actual email sending (SendGrid, etc.)
            logger.info(f"Welcome email sent to patient: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    async def send_therapist_welcome_email(
        self, 
        email: str, 
        first_name: str, 
        license_number: str
    ) -> bool:
        """Send welcome email to therapists"""
        try:
            subject = f"Willkommen bei MindBridge, {first_name}!"
            content = self._get_therapist_template(first_name, license_number)
            
            # TODO: Implement actual email sending
            logger.info(f"Welcome email sent to therapist: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send therapist welcome email: {e}")
            return False
    
    def _get_self_help_patient_template(self, first_name: str) -> str:
        """Email template for self-help patients"""
        return f"""
        Hallo {first_name},
        
        willkommen bei MindBridge! 🌟
        
        Du hast den ersten Schritt für deine mentale Gesundheit gemacht.
        
        Deine Tools:
        • 📊 Stimmungstagebuch
        • 🌙 Traumjournal  
        • 📝 Therapie-Notizen
        • 🤖 KI-Chat Support
        
        Alles funktioniert komplett ohne Therapeut!
        
        Viel Erfolg,
        Dein MindBridge Team
        """
    
    def _get_patient_with_therapist_template(self, first_name: str) -> str:
        """Email template for patients with therapist"""
        return f"""
        Hallo {first_name},
        
        willkommen bei MindBridge! 🌟
        
        Du kannst optional Daten mit deinem Therapeuten teilen.
        
        Alle Tools funktionieren auch ohne Therapeut!
        
        Viel Erfolg,
        Dein MindBridge Team
        """
    
    def _get_therapist_template(self, first_name: str, license_number: str) -> str:
        """Email template for therapists"""
        return f"""
        Hallo {first_name},
        
        willkommen bei MindBridge für Therapeuten!
        
        Ihre Lizenz: {license_number}
        
        Sie können jetzt Share-Keys von Patienten annehmen.
        
        Beste Grüße,
        Das MindBridge Team
        """
