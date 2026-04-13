from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncIterator

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine, desc, select

load_dotenv()

SECRET_KEY = os.getenv("CHAT_SECRET_KEY", "")
ADMIN_USERNAME = os.getenv("CHAT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("CHAT_ADMIN_PASSWORD", "")
DATABASE_URL = os.getenv("CHAT_DATABASE_URL", "sqlite:///./chat.db")
TOKEN_TTL_HOURS = 24 * 7
JWT_ALG = "HS256"

if not SECRET_KEY:
    raise RuntimeError("CHAT_SECRET_KEY must be set in environment")
if not ADMIN_PASSWORD:
    raise RuntimeError("CHAT_ADMIN_PASSWORD must be set in environment")


class User(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    username: str = SQLField(unique=True, index=True)
    password_hash: str
    nickname: str
    is_admin: bool = False
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Message(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="user.id", index=True)
    nickname: str
    content: str
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALG)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALG])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired token"
        ) from e


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.username == ADMIN_USERNAME)
        ).first()
        if existing is None:
            session.add(
                User(
                    username=ADMIN_USERNAME,
                    password_hash=hash_password(ADMIN_PASSWORD),
                    nickname=ADMIN_USERNAME,
                    is_admin=True,
                )
            )
            session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(lifespan=lifespan, title="hanpipette chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session() -> Session:
    with Session(engine) as session:
        yield session


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = decode_token(token)
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    token: str
    user: "UserPublic"


class UserPublic(BaseModel):
    id: int
    username: str
    nickname: str
    is_admin: bool


class NicknameBody(BaseModel):
    nickname: str = Field(min_length=1, max_length=32)


class CreateUserBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=4, max_length=256)
    nickname: str | None = None
    is_admin: bool = False


class MessagePublic(BaseModel):
    id: int
    user_id: int
    nickname: str
    content: str
    created_at: datetime


TokenResponse.model_rebuild()


def to_public_user(u: User) -> UserPublic:
    return UserPublic(
        id=u.id or 0,
        username=u.username,
        nickname=u.nickname,
        is_admin=u.is_admin,
    )


def to_public_message(m: Message) -> MessagePublic:
    return MessagePublic(
        id=m.id or 0,
        user_id=m.user_id,
        nickname=m.nickname,
        content=m.content,
        created_at=m.created_at,
    )


@app.post("/api/auth/login", response_model=TokenResponse)
def login(
    body: LoginBody,
    session: Session = Depends(get_session),
) -> TokenResponse:
    user = session.exec(
        select(User).where(User.username == body.username)
    ).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid username or password"
        )
    assert user.id is not None
    return TokenResponse(token=create_token(user.id), user=to_public_user(user))


@app.get("/api/auth/me", response_model=UserPublic)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return to_public_user(user)


@app.patch("/api/auth/nickname", response_model=UserPublic)
def update_nickname(
    body: NicknameBody,
    user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
) -> UserPublic:
    new_nick = body.nickname.strip()
    if not new_nick:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nickname cannot be empty")
    user.nickname = new_nick
    session.add(user)
    session.commit()
    session.refresh(user)
    return to_public_user(user)


@app.get("/api/messages", response_model=list[MessagePublic])
def list_messages(
    _: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
    before_id: int | None = Query(default=None),
) -> list[MessagePublic]:
    stmt = select(Message).order_by(desc(Message.id)).limit(limit)
    if before_id is not None:
        stmt = stmt.where(Message.id < before_id)
    rows = list(session.exec(stmt).all())
    rows.reverse()
    return [to_public_message(m) for m in rows]


@app.get("/api/users", response_model=list[UserPublic])
def list_users(
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(get_session),
) -> list[UserPublic]:
    rows = session.exec(select(User).order_by(User.id)).all()
    return [to_public_user(u) for u in rows]


@app.post(
    "/api/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
def create_user(
    body: CreateUserBody,
    _: Annotated[User, Depends(require_admin)],
    session: Session = Depends(get_session),
) -> UserPublic:
    username = body.username.strip()
    if not username:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username required")
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    user = User(
        username=username,
        password_hash=hash_password(body.password),
        nickname=(body.nickname or username).strip() or username,
        is_admin=body.is_admin,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return to_public_user(user)


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
    session: Session = Depends(get_session),
) -> None:
    if user_id == admin.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Cannot delete your own admin account"
        )
    target = session.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    session.delete(target)
    session.commit()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self.lock:
            self.active.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self.lock:
            self.active.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        async with self.lock:
            targets = list(self.active)
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def ws_chat(ws: WebSocket, token: str = Query(...)) -> None:
    try:
        user_id = decode_token(token)
    except HTTPException:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    with Session(engine) as session:
        user = session.get(User, user_id)
    if user is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            content = str(data.get("content", "")).strip()
            if not content:
                continue
            if len(content) > 2000:
                content = content[:2000]
            with Session(engine) as session:
                fresh = session.get(User, user_id)
                if fresh is None:
                    break
                msg = Message(
                    user_id=user_id,
                    nickname=fresh.nickname,
                    content=content,
                )
                session.add(msg)
                session.commit()
                session.refresh(msg)
                payload = to_public_message(msg).model_dump(mode="json")
            await manager.broadcast(payload)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)
