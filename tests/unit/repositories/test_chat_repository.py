import pytest
from sqlalchemy.ext.asyncio import AsyncSession
# from app.repositories.chat_repository import ChatRepository
# from app.schemas.chat import SessionCreate, MessageCreate


@pytest.fixture
async def test_user(db_session: AsyncSession):
    from app.models.user import User
    import uuid

    email = f"chat_{uuid.uuid4()}@example.com"
    user = User(email=email, hashed_password="hashed_password", full_name="Chat Owner")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user):
    from app.models.project import Project

    project = Project(name="Chat Project", owner_id=test_user.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_create_session(db_session: AsyncSession, test_project):
    """
    Test creating a chat session for a project.
    """
    from app.repositories.chat_repository import ChatRepository
    from app.schemas.chat import SessionCreate

    repo = ChatRepository(db_session)
    session_in = SessionCreate(project_id=test_project.id)
    session = await repo.create_session(session_in)

    assert session.id is not None
    assert session.project_id == test_project.id


@pytest.mark.asyncio
async def test_add_message_to_session(db_session: AsyncSession, test_project):
    """
    Test adding messages to a chat session.
    """
    from app.repositories.chat_repository import ChatRepository
    from app.schemas.chat import SessionCreate, MessageCreate

    repo = ChatRepository(db_session)
    chat_session = await repo.create_session(SessionCreate(project_id=test_project.id))

    # User message
    msg_user = await repo.add_message(
        chat_session.id, MessageCreate(role="user", content="Hello IA")
    )

    # IA message
    msg_ai = await repo.add_message(
        chat_session.id, MessageCreate(role="assistant", content="Hello Human")
    )

    assert msg_user.id is not None
    assert msg_ai.content == "Hello Human"

    # Verify history retrieval
    history = await repo.get_history(chat_session.id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"
