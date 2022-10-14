from flask_sqlalchemy import SQLAlchemy
from medsenger_api import AgentApiClient


class Manager:
    def __init__(self, medsenger_api: AgentApiClient, db: SQLAlchemy):
        self.medsenger_api = medsenger_api
        self.db = db

    def __commit__(self):
        self.db.session.commit()
