from pydantic import BaseModel, Field, field_validator

class IdentityCanon(BaseModel):
    immutable_identity: bool = True
    standalone_image_only: bool = True
    gauge_terminal_inches: float = Field(default=5.0, ge=1.0, le=5.0)
    protected_back_text: str = "RARE ONE"
    default_chain_required: bool = True

    @field_validator("protected_back_text")
    @classmethod
    def exact_rare_one(cls, value: str) -> str:
        if value != "RARE ONE":
            raise ValueError("protected_back_text must remain exactly 'RARE ONE'")
        return value

CANON = IdentityCanon()
