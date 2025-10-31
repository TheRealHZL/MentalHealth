"""
Base Schema Classes

Basis-Klassen für Pydantic Schemas mit angepasster Konfiguration.
"""

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """
    Basis-Schema-Klasse mit angepasster Konfiguration

    Diese Klasse deaktiviert Pydantic's geschützte Namespaces,
    um Konflikte mit Feldern wie 'model_name', 'model_type' etc. zu vermeiden.
    """

    class Config:
        # Deaktiviere geschützte Namespaces um model_ Konflikte zu vermeiden
        protected_namespaces = ()

        # JSON Schema Anpassungen (für Pydantic v2 Kompatibilität)
        json_schema_extra = None

        # Standard Konfiguration
        validate_assignment = True
        use_enum_values = True
        populate_by_name = True
