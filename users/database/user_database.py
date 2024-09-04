from pathlib import Path
src_path = Path(__file__).resolve().parent.parent.parent
import sys
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
from src.backend import config
from src.backend.utils.sqlalchemy_tool import get_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = get_engine(config.USER_DATABASE)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
