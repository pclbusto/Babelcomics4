from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///data/babelcomics.db', echo=False)
Base = declarative_base()

from entidades.publisher_model import Publisher
from entidades.setup_model import Setup
from entidades.volume_model import Volume