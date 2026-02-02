"""Many-to-Many 관계를 위한 Link 모델들"""

from sqlmodel import Field, SQLModel


class ConversationMemoryLink(SQLModel, table=True):
    """Conversation-Memory Many-to-Many Link"""

    __tablename__ = "conversation_memory_link"

    conversation_id: int = Field(foreign_key="conversation.id", primary_key=True)
    memory_id: int = Field(foreign_key="memory.id", primary_key=True)


class ConversationReminderLink(SQLModel, table=True):
    """Conversation-Reminder Many-to-Many Link"""

    __tablename__ = "conversation_reminder_link"

    conversation_id: int = Field(foreign_key="conversation.id", primary_key=True)
    reminder_id: int = Field(foreign_key="reminder.id", primary_key=True)
