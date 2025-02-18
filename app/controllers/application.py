from app.controllers.db.datamanager import DataManager

class Application:
    def __init__(self):
        self.pages = {}
        self.db = DataManager()

