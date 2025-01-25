import io
import logging
import os
import sys
import time

import folium
import serial
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .database import Database
from .helper import local_path
from .player import Player
from .server import KartClient, KartServer
from .web import WebService


class PlayerMap(QWidget):
    def __init__(self, database, ip, port):
        super().__init__()

        self.database = Database(database)
        self.database.post_init()
        self.newest = None

        KartServer(ip, port, database)

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

    def updateCoordinates(self):
        logging.debug("Updating Coords")

        gps = self.database.select_my_newest_point()
        if gps:
            if self.newest:
                if self.newest.id != gps.id:
                    self._set_coordlabel_and_newest(gps)
            else:
                self._set_coordlabel_and_newest(gps)

    def _set_coordlabel_and_newest(self, gps):
        target = self.database.game.target
        self.coordLabel.setText(f"Coordinates: (X: {gps.x}, Y: {gps.y})")
        self.textField.setText(
            f"Distance to Target: {int(gps.distance(target))}m"
        )  # Update new text field
        self.updateMap(gps, target, self.database.active_players)
        self.newest = gps

    def updateMap(self, gps, target, players: list[Player] = []):
        # Create a Folium map
        folium_map = folium.Map(location=[gps.x, gps.y], zoom_start=10)

        folium.Marker([gps.x, gps.y], popup="Current Location").add_to(folium_map)

        folium.Marker(
            [target.x, target.y], popup="Target", icon=folium.Icon(color="red")
        ).add_to(folium_map)

        player_group = folium.FeatureGroup("Player Group").add_to(folium_map)
        for player in players:
            points = player.newest_point(self.database)
            folium.Marker(points.as_list(), popup=str(player.id)).add_to(player_group)

        trail_coordinates = [gps.as_list(), target.as_list()]
        folium.PolyLine(trail_coordinates, tooltip="Coast").add_to(folium_map)

        map_file = f"{local_path}/map.html"
        folium_map.save(map_file)

        html_map = QUrl.fromLocalFile(os.path.abspath(map_file))
        self.map_view.page().settings().setAttribute(
            QWebEngineSettings.LocalContentCanAccessRemoteUrls, True
        )
        self.map_view.load(html_map)


def start(database, ip, port):
    web = WebService()
    web.start()
    app = QApplication(sys.argv)
    ex = PlayerMap(database, ip, port)
    sys.exit(app.exec_())
