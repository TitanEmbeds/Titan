from contextlib import contextmanager
from asyncio_extras import threadpool
import sqlalchemy as db
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from titanembeds.database.guilds import Guilds

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
