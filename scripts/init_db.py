from app.db.base import Base
from app.db.session import engine
from app.models import *  # noqa: F401, F403


def init():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    init()
