import io
import logging
import os
import sys
import time

import folium
import serial
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .gps import place
from .database import Database
from .helper import local_path
from .player import Player, PlayerPoints
from .server import KartClient, KartServer
from .web import WebService


class PlayerMap(QWidget):
    def __init__(self, database, ip, port, args):
        super().__init__()

        self.database = Database(database)
        self.database.post_init()
        self.newest = None

        self.server = KartServer(ip, port, database, args)

        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateCoordinates)
        self.timer.start(5000)  # Update every 5000 ms (5 seconds)

        self.current_coordinates = (0, 0)

    def initUI(self):
        # Layouts
        mainLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()

        # Coordinate display
        self.coordLabel = QLabel("Coordinates: (Lat: 0, Lon: 0)")
        leftLayout.addWidget(self.coordLabel)

        # Text field to update
        self.textField = QLabel("")  # New text field
        leftLayout.addWidget(self.textField)

        self.placeField = QLabel("")  # New text field
        leftLayout.addWidget(self.placeField)

        # Folium map display
        self.map_view = QWebEngineView()

        mainLayout.addLayout(leftLayout)
        mainLayout.addWidget(self.map_view)

        self.setLayout(mainLayout)

        self.setWindowTitle("Coordinate Logger")
        self.setGeometry(100, 100, 800, 600)
        self.show()

        self.newest = self.database.select_my_newest_point()
        # Initial map display
        if self.newest:
            self.updateMap(self.newest, self.database.game.target)

        self.showFullScreen()

    def updateCoordinates(self):
        logging.debug("Updating Coords")

        gps = self.database.select_my_newest_point()
        self._set_coordlabel_and_newest()

    def _set_coordlabel_and_newest(self):
        players = self.database.select_active_players()
        me = self.database.select_my_newest_point()
        target = self.database.game.target
        self.coordLabel.setText(f"Coordinates: (X: {me.x}, Y: {me.y})")
        self.textField.setText(
            f"Distance to Target: {int(me.distance(target[0]))}m"
        )  # Update new text field
        self.newest = me
        self.updateMap(target, players)

    def updateMap(self, target, players: list[PlayerPoints] = []):
        pick_me = [player for player in players if player.me]
        if len(pick_me) > 0:
            me = pick_me[0]
            print(me.points)

            # Create a Folium map
            folium_map = folium.Map(location=me.points[0].as_list(), zoom_start=18)

            for gps in target:
                folium.Marker(
                    [gps.x, gps.y], popup="Target", icon=folium.Icon(color="red")
                ).add_to(folium_map)

            player_group = folium.FeatureGroup("Player Group").add_to(folium_map)
            for player in players:
                points = None
                if len(player.points) > 0:
                    points = player.points[0]
                else:
                    print(f"Player points could not be updated {player}")
                    continue
                if player.me:
                    folium.Marker(points.as_list(), popup="Current Location").add_to(
                        player_group
                    )
                else:
                    folium.Marker(points.as_list(), popup=str(player.id)).add_to(
                        player_group
                    )

            my_place = place(
                me.points[0],
                [player.points[0] for player in players if len(player.points) > 0],
                target[0],
            )
            self.placeField.setText(f"My Place: {my_place}")

            trail_coordinates = [me.points[0].as_list(), target[0].as_list()]
            folium.PolyLine(trail_coordinates, tooltip="Coast").add_to(folium_map)

            map_file = f"{local_path}/map.html"
            folium_map.save(map_file)

            html_map = QUrl.fromLocalFile(os.path.abspath(map_file))
            self.map_view.page().settings().setAttribute(
                QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
            )
            self.map_view.load(html_map)


def start_gui(database, ip, port, args):
    web = WebService()
    web.start()
    app = QApplication(sys.argv)
    ex = PlayerMap(database, ip, port, args)
    sys.exit(app.exec_())
