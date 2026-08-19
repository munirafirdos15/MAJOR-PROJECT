from pydantic import BaseModel, EmailStr, Field


class UserRegistrationRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    first_name: str = Field(
        min_length=1,
        max_length=100
    )

    last_name: str | None = Field(
        default=None,
        max_length=100
    )

    mobile_number: str | None = Field(
        default=None,
        max_length=20
    )


class UserRegistrationResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str | None
    email_verified: bool


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserLoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )

    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str
    session_id: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str | None
    last_name: str | None
    email_verified: bool
    roles: list[str]
    