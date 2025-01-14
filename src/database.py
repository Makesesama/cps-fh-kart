import sqlite3
import uuid

from .player import Player


class Database:
    __db_path: str
    me: Player

    def __init__(self, database_path: str):
        self.__db_path = database_path
        self.__con = sqlite3.connect(self.__db_path)
        self.me = self.get_my_player()

    def __cursor(self):
        return self.__con.cursor()

    def get_my_player(self):
        cursor = self.__cursor()

        db_player = cursor.execute(
            "SELECT id, me FROM players WHERE me=TRUE"
        ).fetchone()
        if len(db_player) > 0:
            (id, me) = db_player
            return Player(id, me)
        else:
            self.create_new_player(uuid.uuid4(), me=True)

    def create_tables(self):
        cursor = self.__cursor()
        cursor.execute("CREATE TABLE location_data(id, x, y, created_at, player_id)")
        cursor.execute("CREATE TABLE players(id, active, me)")

    def create_new_player(self, id, me=False):
        return Player()
