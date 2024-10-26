from pydantic import BaseModel

class UserInfo(BaseModel):
    user_id: str
    deposit_token: str