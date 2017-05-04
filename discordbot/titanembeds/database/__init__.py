from config import config
from sqlalchemy_aio import ASYNCIO_STRATEGY
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .guilds import Guilds

engine = db.create_engine(config["database-uri"])

Base.metadata.create_all(engine)

from sqlalchemy.orm import sessionmaker
DBSession = sessionmaker()
DBSession.bind = engine
session = DBSession()