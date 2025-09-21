"""Email result data model."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Contact:
    "represnts a persons contact"

    name: str
    company_name: str
    email: str
    position: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "company_name": self.company_name,
            "email": self.email,
            "position": self.position,
        }


@dataclass
class EmailResult:
    """Represents emails found for a domain."""

    domain: str
    emails: List[Contact]
    finder: str
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        # This is the key change. We iterate over the list of Contact objects
        # and call .to_dict() on each one.
        serialized_emails = [contact.to_dict() for contact in self.emails]

        return {
            "domain": self.domain,
            "emails": serialized_emails,  # Use the new, serialized list
            "finder": self.finder,
            "success": self.success,
            "error": self.error,
        }
