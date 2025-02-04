import logging
import sqlite3
import uuid
from datetime import datetime

import msgspec

from .game import Game
from .gps import DBGPS, GPSBase, Track
from .payload import Payload
from .player import Player, PlayerPoints


class DBInfo(msgspec.Struct):
    path: str
    game: Game
    track: Track


class DBWrapper:
    def __init__(self, db_info: DBInfo):
        self.database = Database(db_info)
        self.exit = False


class Database:
    """Homebrew database abstraction.

    Connects to sqlite, creates tables and handles all the application data
    """

    __db_path: str
    me: Player
    game: Game
    track: Track
    active_players: list[Player] = []

    def __init__(self, database: DBInfo):
        self.__db_path = database.path
        self.game = database.game
        self.track = database.track

    @classmethod
    def for_pre_init(self, database: str, args):
        db = Database(
            DBInfo(
                database,
                Game(0, target=[GPSBase(54.332262, 10.180552)]),
                Track(args.track_path),
            )
        )
        db.connect()
        db.create_tables()
        db.flash_all_players()

        game = db.select_newest_game()
        game_id = 0
        if game:
            game_id = game.id + 1

        track = Track(args.track_path)

        # [
        #     GPSBase(args.target_gps_x, args.target_gps_y),
        #     GPSBase(args.target_gps_x + 0.001, args.target_gps_y + 0.001),
        # ],
        game = Game(game_id, target=track.gps_data)
        db.insert_game(game)
        db.commit()

        return game, track

    def connect(self):
        self.__con = sqlite3.connect(self.__db_path)

    def post_init(self):
        """Initiates DB connection.

        This is needed so all threads can initiate their own db connections.
        """
        self.connect()
        self.me = self.get_my_player_and_game()

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
            "CREATE TABLE IF NOT EXISTS location_data(id TEXT PRIMARY KEY, x REAL, y REAL, created_at TIMESTAMP, player_id TEXT, game_id INTEGER, is_target BOOLEAN DEFAULT FALSE)",
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
        WHERE game_id = ? AND player_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """
        db_active_players = cursor.execute(player_query).fetchall()

        active_players = []

        for player in db_active_players:
            locations = cursor.execute(
                point_query,
                (
                    self.game.id,
                    str(player[0]),
                ),
            ).fetchall()
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

    def game_parser(self, rows):
        return Game(
            rows[0][0], target=[GPSBase(target[1], target[2]) for target in rows]
        )

    def select_game(self, id) -> Game:
        query = """
        SELECT games.id, x, y FROM games
        JOIN location_data ON games.id = location_data.game_id
        WHERE games.id = ? AND is_target = TRUE
        """
        cursor = self.__cursor()
        result = cursor.execute(
            query,
            (id,),
        ).fetchall()
        game = self.game_parser(result)
        return game

    def select_newest_game(self) -> Game | None:
        query = """
        SELECT games.id, x, y FROM games
        JOIN location_data ON games.id = location_data.game_id
        WHERE is_target = TRUE
        ORDER BY games.id DESC LIMIT 1
        """
        cursor = self.__cursor()
        result = cursor.execute(query).fetchall()
        if len(result) < 1:
            return None
        return self.game_parser(result)

    def insert_game(self, game: Game):
        query = (
            "INSERT INTO games (id, target_x, target_y, created_at) VALUES (?, ?, ?, ?)"
        )

        points_query = """
        INSERT INTO location_data (id, x, y, created_at, player_id, game_id, is_target) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.__cursor()

        cursor.execute(
            query,
            (
                game.id,
                0,
                0,
                datetime.now(),
            ),
        )

        cursor.executemany(points_query, game.target_as_tuples(game.id))

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
