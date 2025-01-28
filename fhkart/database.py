import logging
import sqlite3
import uuid
from datetime import datetime

import msgspec

from .game import Game
from .gps import DBGPS, GPSBase
from .payload import Payload
from .player import Player, PlayerPoints


class DBInfo(msgspec.Struct):
    path: str
    game: Game


class Database:
    """Homebrew database abstraction.

    Connects to sqlite, creates tables and handles all the application data
    """

    __db_path: str
    me: Player
    game: Game
    active_players: list[Player] = []

    def __init__(self, database: DBInfo):
        self.__db_path = database.path
        self.game = database.game

    def post_init(self):
        """Initiates DB connection.

        This is needed so all threads can initiate their own db connections.
        """
        self.__con = sqlite3.connect(self.__db_path)
        self.me = self.get_my_player_and_game()
        self.flash_all_players()

    def __cursor(self):
        return self.__con.cursor()

    def commit(self):
        self.__con.commit()

    def get_my_player_and_game(self):
        """Gets this player out of db.

        Loads it into database class so we can use it
        """
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

        self.commit()
        if db_player is not None:
            (id, address, me) = db_player
            return Player(id, address)
        else:
            return self.create_new_player(uuid.uuid4(), "localhost", me=True)

    def create_tables(self):
        """Create tables."""
        queries = [
            "CREATE TABLE IF NOT EXISTS location_data(id TEXT PRIMARY KEY, x REAL, y REAL, created_at TIMESTAMP, player_id TEXT, game_id INTEGER)",
            "CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY, active BOOLEAN, me BOOLEAN, address TEXT)",
            "CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY, target_x REAL, target_y REAL, created_at TIMESTAMP)",
        ]
        cursor = self.__cursor()
        for query in queries:
            cursor.execute(query)
        self.commit()

    def flash_all_players(self):
        """Sets all players to unactive.

        At start set all players that are not me to unactive
        """
        cursor = self.__cursor()
        query = "UPDATE players SET active=false WHERE me=false"
        cursor.execute(query)
        self.commit()

    def check_player_and_insert(self, player):
        if not self.check_player(player):
            logging.debug(f"Added new active Player {player}")
            player = self.create_new_player(player.id, player.address)
        self.active_players.append(player)
        return player

    def check_player(self, player):
        cursor = self.__cursor()
        update_query = "UPDATE players SET active=true WHERE id = ?"
        select_query = "SELECT id, address, active, me FROM players WHERE id = ?"

        db_player = cursor.execute(select_query, (str(player.id),)).fetchone()
        if db_player is None:
            return False

        if not bool(db_player[2]):
            cursor.execute(update_query, (str(player.id),))
            logging.info(
                f"New Player joined the Game! Current player: {len(self.active_players)}"
            )
            self.commit()
        return True

    def create_new_player(self, id, address, me=False):
        player = Player(id, address, True, me)
        self.insert_player(player)
        self.commit()
        logging.info(
            f"New Player joined the Game! Current player: {len(self.active_players)}"
        )
        return player

    def create_new_game(self, id=0):
        self.insert_game(id)
        self.commit()
        return id

    def select_active_players(self):
        cursor = self.__cursor()
        player_query = """
        SELECT id, address, active, me FROM players
        WHERE active=true
        """
        point_query = """
        SELECT x, y, id, created_at FROM location_data
        WHERE game_id = 100 AND player_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """
        db_active_players = cursor.execute(player_query).fetchall()

        active_players = []

        for player in db_active_players:
            locations = cursor.execute(point_query, (str(player[0]),)).fetchall()
            active_players.append(
                PlayerPoints(
                    id=player[0],
                    address=player[1],
                    active=bool(player[2]),
                    me=bool(player[3]),
                    points=[DBGPS(gps[0], gps[1], gps[2], gps[3]) for gps in locations],
                )
            )

        self.active_players = active_players
        return active_players

    def select_newest_point(self, player_id) -> DBGPS | None:
        """Selects my newest gps data."""
        cursor = self.__cursor()
        query = "SELECT id, x, y, created_at FROM location_data WHERE player_id = ? AND game_id = ? ORDER BY created_at DESC LIMIT 1"

        db_point = cursor.execute(
            query,
            (
                str(player_id),
                str(self.game.id),
            ),
        ).fetchone()
        if not db_point:
            return None
        (id, x, y, created_at) = db_point
        return DBGPS(x, y, id, created_at)

    def select_my_newest_point(self) -> DBGPS | None:
        return self.select_newest_point(self.me.id)

    def select_game(self, id) -> Game:
        cursor = self.__cursor()
        (game_id, target_x, target_y) = cursor.execute(
            "SELECT id, target_x, target_y FROM games WHERE id = ?",
            (id,),
        ).fetchone()
        return Game(game_id, target=GPSBase(target_x, target_y))

    def select_newest_game(self) -> Game | None:
        cursor = self.__cursor()
        result = cursor.execute(
            "SELECT id, target_x, target_y FROM games ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not result:
            return None
        (game_id, target_x, target_y) = result
        return Game(game_id, target=GPSBase(target_x, target_y))

    def insert_game(self, game: Game):
        query = (
            "INSERT INTO games (id, target_x, target_y, created_at) VALUES (?, ?, ?, ?)"
        )
        cursor = self.__cursor()

        cursor.execute(
            query,
            (
                game.id,
                datetime.now(),
                game.target.x,
                game.target.y,
            ),
        )
        return game

    def insert_player(self, player):
        query = "INSERT INTO players (id, address, active, me) VALUES (?, ?, ?, ?)"
        cursor = self.__cursor()

        cursor.execute(
            query, (str(player.id), player.address, player.active, player.me)
        )

    def insert_gps(self, gps, player):
        """Inserts gps data.

        Ignores it if it already exists in the database
        """
        query = "INSERT OR IGNORE INTO location_data (id, x, y, created_at, player_id, game_id) VALUES (?, ?, ?, ?, ?, ?)"
        cursor = self.__cursor()

        cursor.execute(
            query,
            (
                str(gps.id),
                gps.x,
                gps.y,
                datetime.now(),
                str(player.id),
                self.game.id,
            ),
        )

    def insert_payload(self, payload: Payload):
        player = self.check_player_and_insert(payload.player)
        if not player.me:
            self.insert_gps(payload.gps, payload.player)
        self.commit()
