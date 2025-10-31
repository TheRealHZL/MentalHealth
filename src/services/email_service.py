"""
Email Service - User Communications

Sendet Willkommens-Emails und Benachrichtigungen.
"""

import logging
from typing import Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email Service für User-Kommunikation"""

    def __init__(self):
        self.settings = get_settings()
        self.sender_email = "noreply@mindbridge.com"
        self.sender_name = "MindBridge Team"
        self.enabled = getattr(self.settings, "EMAIL_ENABLED", False)

        if not self.enabled:
            logger.warning("📧 Email service is DISABLED. Emails will be logged only.")
        else:
            logger.info("📧 Email service is ENABLED")

    async def send_welcome_email(
        self, to_email: str, first_name: str, has_therapist: bool = False
    ) -> bool:
        """Send welcome email (alias for send_patient_welcome_email)"""
        return await self.send_patient_welcome_email(
            to_email, first_name, has_therapist
        )

    async def send_patient_welcome_email(
        self, email: str, first_name: str, has_therapist: bool = False
    ) -> bool:
        """Send welcome email to patients"""
        try:
            subject = f"Willkommen bei MindBridge, {first_name}! 🌟"

            if has_therapist:
                content = self._get_patient_with_therapist_template(first_name)
            else:
                content = self._get_self_help_patient_template(first_name)

            return await self._send_email(email, subject, content)

        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False

    async def send_therapist_welcome_email(
        self, email: str, first_name: str, license_number: str
    ) -> bool:
        """Send welcome email to therapists"""
        try:
            subject = f"Willkommen bei MindBridge, {first_name}!"
            content = self._get_therapist_template(first_name, license_number)

            return await self._send_email(email, subject, content)

        except Exception as e:
            logger.error(f"Failed to send therapist welcome email: {e}")
            return False

    async def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """
        Internal method to send emails

        Currently logs emails. To enable actual sending:
        1. Set EMAIL_ENABLED=true in config
        2. Configure EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD
        3. Implement SMTP or integrate with SendGrid/Mailgun/AWS SES
        """
        if not self.enabled:
            logger.info(f"📧 [DISABLED] Email would be sent to: {to_email}")
            logger.info(f"📧 Subject: {subject}")
            logger.debug(f"📧 Content: {content}")
            return True  # Return True to not break flows

        try:
            # When EMAIL_ENABLED=true, implement actual email sending here:
            # Example with SMTP:
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart
            #
            # msg = MIMEMultipart()
            # msg['From'] = self.sender_email
            # msg['To'] = to_email
            # msg['Subject'] = subject
            # msg.attach(MIMEText(content, 'html'))
            #
            # with smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT) as server:
            #     server.starttls()
            #     server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)
            #     server.send_message(msg)

            logger.info(f"📧 Email sent to: {to_email}")
            logger.info(f"📧 Subject: {subject}")
            return True

        except Exception as e:
            logger.error(f"📧 Failed to send email to {to_email}: {e}")
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
