import sqlite3
import uuid
from datetime import datetime

from .player import Player
from .payload import Payload


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
        if db_player is not None:
            (id, me) = db_player
            return Player(id, me)
        else:
            return self.create_new_player(uuid.uuid4(), me=True)

    def create_tables(self):
        cursor = self.__cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS location_data(id TEXT PRIMARY KEY, x REAL, y REAL, created_at TEXT, player_id TEXT)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY, active BOOLEAN, me BOOLEAN)"
        )
        cursor.commit()

    def create_new_player(self, id, me=False):
        player = Player(id, me)
        self.insert_player(player)
        return player

    def insert_player(self, player):
        query = "INSERT INTO players (id, active, me) VALUES (?, ?, ?)"
        cursor = self.__cursor()

        cursor.execute(query, (str(player.id), player.active, player.me))
        self.__con.commit()

    def insert_payload(self, payload: Payload):
        query = "INSERT INTO location_data (id, x, y, created_at, player_id) VALUES (?, ?, ?, ?, ?)"
        cursor = self.__cursor()

        cursor.execute(
            query,
            (
                str(uuid.uuid4()),
                payload.gps.x,
                payload.gps.y,
                datetime.now(),
                str(payload.player_id),
            ),
        )
        self.__con.commit()
