import logging
import sqlite3
import uuid
from datetime import datetime

from .gps import DBGPS
from .payload import Payload
from .player import Player


class Database:
    __db_path: str
    me: Player

    def __init__(self, database_path: str):
        self.__db_path = database_path

    def post_init(self):
        self.__con = sqlite3.connect(self.__db_path)
        self.me = self.get_my_player()
        self.flash_all_players()

    def __cursor(self):
        return self.__con.cursor()

    def _commit(self):
        self.__con.commit()

    def get_my_player(self):
        cursor = self.__cursor()
        try:
            db_player = cursor.execute(
                "SELECT id, address, me FROM players WHERE me=TRUE"
            ).fetchone()
        except sqlite3.OperationalError:
            self.create_tables()
            db_player = cursor.execute(
                "SELECT id, address, me FROM players WHERE me=TRUE"
            ).fetchone()
        if db_player is not None:
            (id, address, me) = db_player
            return Player(id, address)
        else:
            return self.create_new_player(uuid.uuid4(), "localhost", me=True)

    def create_tables(self):
        cursor = self.__cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS location_data(id TEXT PRIMARY KEY, x REAL, y REAL, created_at TIMESTAMP, player_id TEXT)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY, active BOOLEAN, me BOOLEAN, address TEXT)"
        )
        self._commit()

    def flash_all_players(self):
        cursor = self.__cursor()
        query = "UPDATE players SET active=false WHERE me=false"
        cursor.execute(query)
        self._commit()

    def check_player_and_insert(self, player):
        if not self.check_player(player):
            logging.info(f"Added new active Player {player}")
            self.create_new_player(player.id, player.address)
        return player

    def check_player(self, player):
        cursor = self.__cursor()
        update_query = "UPDATE players SET active=true WHERE id = ?"
        select_query = "SELECT id, address, active FROM players WHERE id = ?"

        db_player = cursor.execute(select_query, (str(player.id),)).fetchone()
        if db_player is None:
            return False

        if not bool(db_player[2]):
            cursor.execute(update_query, (str(player.id),))
            self._commit()
        return True

    def create_new_player(self, id, address, me=False):
        player = Player(id, address, me)
        self.insert_player(player)
        return player

    def select_active_players(self):
        cursor = self.__cursor()
        query = "SELECT id, address, active FROM players WHERE active=true AND me=false"
        db_active_players = cursor.execute(query).fetchall()

        return [Player(player[0], player[1], player[2]) for player in db_active_players]

    def select_my_newest(self):
        cursor = self.__cursor()
        query = "SELECT id, x, y, created_at FROM location_data WHERE player_id = ? ORDER BY created_at DESC LIMIT 1"
        db_point = cursor.execute(query, (self.me.id,)).fetchone()
        (id, x, y, created_at) = db_point
        return DBGPS(x, y, id, created_at)

    def insert_player(self, player):
        query = "INSERT INTO players (id, address, active, me) VALUES (?, ?, ?, ?)"
        cursor = self.__cursor()

        cursor.execute(
            query, (str(player.id), player.address, player.active, player.me)
        )
        self._commit()

    def insert_gps(self, gps, player):
        # Insert a new gps or ignore if it already exists
        query = "INSERT OR IGNORE INTO location_data (id, x, y, created_at, player_id) VALUES (?, ?, ?, ?, ?)"
        cursor = self.__cursor()

        cursor.execute(
            query,
            (
                str(uuid.uuid4()),
                gps.x,
                gps.y,
                datetime.now(),
                str(player.id),
            ),
        )
        self._commit()

    def insert_payload(self, payload: Payload):
        self.insert_gps(payload.gps, payload.player)
        self.check_player_and_insert(payload.player)
        self._commit()
