import hashlib
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator

def sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()



class SurveySubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    user_agent: Optional[str] = Field( default=None, description="Browser or client identifier (optional)." )
    age: int = Field(..., ge=13, le=120)
    consent: bool = Field(..., description="Must be true to accept")
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=1000)
    submission_id: Optional[str] = Field(default=None)
  

 


    @validator("comments")
    def _strip_comments(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("consent")
    def _must_consent(cls, v):
        if v is not True:
            raise ValueError("consent must be true")
        return v

    @validator("submission_id", pre=False, always=True)
    def assign_submission_id(cls, v, values):
        if v is not None:
            return v

        email = values.get("email")
        if email is None:
            return None
        
        timestamp = datetime.utcnow().strftime("%Y%m%d%H")
        raw_string = f"{email}{timestamp}"
        return sha256_hash(raw_string)
        
#Good example of inheritance
class StoredSurveyRecord(SurveySubmission):
    received_at: datetime
    ip: str
