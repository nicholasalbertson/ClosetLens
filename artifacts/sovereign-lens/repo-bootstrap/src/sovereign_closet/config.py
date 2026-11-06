from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    app_name: str = "Sovereign Closet"
    default_currency: str = "USD"
    proof_jobs_billable: bool = False

settings = Settings()
