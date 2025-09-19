"""Email result data model."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmailResult:
    """Represents emails found for a domain."""
    domain: str
    emails: List[str]
    finder: str
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "domain": self.domain,
            "emails": self.emails,
            "finder": self.finder,
            "success": self.success,
            "error": self.error,
        }