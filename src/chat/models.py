from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
import uuid

class Message(SQLModel, table=True):
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    channel_id: str = Field(index=True)
    sender: str
    content: str
    message_type: str = Field(default="message")
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))