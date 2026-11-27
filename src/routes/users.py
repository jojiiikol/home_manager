from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from src.exceptions.users import (
    IncorrectPassword,
    InvalidCredentials,
    UsernameAlreadyExists,
    UserNotFound,
)
from src.routes.dependencies import CurrentUser, UsersServiceDependency
from src.schemas.passwords import ChangePasswordRequest
from src.schemas.users import (
    LoginRequest,
    PublicUserResponse,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

router = APIRouter(tags=["users"])


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(
    body: RegisterRequest, service: UsersServiceDependency
) -> UserResponse:
    try:
        user = await service.register(body.username, body.password.get_secret_value())
    except UsernameAlreadyExists:
        raise HTTPException(status_code=409, detail="Username already exists") from None
    return UserResponse.model_validate(user)


@router.post("/auth/token", response_model=TokenResponse)
async def login(body: LoginRequest, service: UsersServiceDependency) -> TokenResponse:
    try:
        token = await service.authenticate(
            body.username, body.password.get_secret_value()
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return TokenResponse(access_token=token.value, expires_in=token.expires_in)


@router.get("/users/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/users/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    service: UsersServiceDependency,
) -> UserResponse:
    user = await service.update_profile(current_user.id, body.name)
    return UserResponse.model_validate(user)


@router.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    service: UsersServiceDependency,
) -> Response:
    try:
        await service.change_password(
            current_user.id,
            body.old_password.get_secret_value(),
            body.new_password.get_secret_value(),
        )
    except IncorrectPassword:
        raise HTTPException(status_code=400, detail="Incorrect old password") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}", response_model=PublicUserResponse)
async def get_user(
    user_id: UUID, current_user: CurrentUser, service: UsersServiceDependency
) -> PublicUserResponse:
    try:
        user = await service.get_profile(user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found") from None
    return PublicUserResponse.model_validate(user)
