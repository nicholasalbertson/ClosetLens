from pydantic import BaseModel
from sovereign_closet.canon.progression import ProgressionLevel

class ProofJob(BaseModel):
    outfit_id: str
    progression_level: ProgressionLevel
    billable: bool = False
    provider: str | None = None
    status: str = "queued"
