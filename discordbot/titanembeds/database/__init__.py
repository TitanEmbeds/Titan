from contextlib import contextmanager
from asyncio_extras import threadpool
import sqlalchemy as db
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

import json

Base = declarative_base()

from titanembeds.database.guilds import Guilds
from titanembeds.database.messages import Messages

class DatabaseInterface(object):
    # Courtesy of https://github.com/SunDwarf/Jokusoramame
    def __init__(self, bot):
        self.bot = bot

        self.engine = None  # type: Engine
        self._sessionmaker = None  # type: sessionmaker

    async def connect(self, dburi):
        async with threadpool():
            self.engine = create_engine(dburi)
            self._sessionmaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def get_session(self) -> Session:
        session = self._sessionmaker()  # type: Session
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    async def push_message(self, message):
        if message.server:
            async with threadpool():
                with self.get_session() as session:
                    edit_ts = message.edited_timestamp
                    if not edit_ts:
                        edit_ts = None
                    else:
                        edit_ts = str(edit_ts)

                    msg = Messages(
                        message.server.id,
                        message.channel.id,
                        message.id,
                        message.content,
                        str(message.timestamp),
                        edit_ts,
                        json.dumps(message.mentions),
                        json.dumps(message.attachments)
                    )
                    session.add(msg)
                    session.commit()

    async def update_message(self, message):
        if message.server:
            async with threadpool():
                with self.get_session() as session:
                    msg = session.query(Messages) \
                        .filter(Messages.guild_id == message.server.id) \
                        .filter(Messages.channel_id == message.channel.id) \
                        .filter(Messages.message_id == message.id).first()
                    if msg:
                        msg.content = message.content
                        msg.edited_timestamp = message.edited_timestamp
                        msg.mentions = json.dumps(message.mentions)
                        msg.attachments = json.dumps(message.attachments)
                        session.commit()
