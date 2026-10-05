from pydantic import BaseModel, Field, ConfigDict
from app.models import UserRole

class UserBase(BaseModel):
    username: str= Field(min_length= 3, max_length=25)
    role: UserRole

class UserCreate(UserBase):
    password: str= Field(min_length= 8)
    name: str= Field(min_length=4, max_length= 75)

class UserRead(UserBase):
    id: int
    name: str= Field(min_length=4, max_length= 75)
    model_config= ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: str | None= Field(default= None, min_length= 3, max_length=25)
    name: str | None= Field(default= None, min_length=4, max_length= 75)
    role: UserRole | None = None

class Token(BaseModel):
    access_token: str
    token_type: str= "bearer"
