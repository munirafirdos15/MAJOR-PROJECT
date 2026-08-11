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
