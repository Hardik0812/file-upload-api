from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: str


# Pydantic model for setting new password
class NewPasswordRequest(BaseModel):
    new_password: str
