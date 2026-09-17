from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class WorkflowEntry:
    workflow: str
    platform: str
    popularity_metrics: Dict[str, Any]
    country: str
    popularity_score: float = 0.0
    source_url: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "workflow": self.workflow,
            "platform": self.platform,
            "popularity_score": round(self.popularity_score, 2),
            "popularity_metrics": self.popularity_metrics,
            "country": self.country,
        }
        if self.source_url:
            data["source_url"] = self.source_url
        if self.id:
            data["id"] = self.id
        return data
