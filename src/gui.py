import io
import logging
import os
import sys
import time

import folium
import serial
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .server import KartClient


class CoordinateLogger(QWidget):
    def __init__(self, database, ip, port):
        super().__init__()

        self.database = Database(database)
        self.database.post_init()
        self.newest = None

        KartClient(ip, port, database, False)

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

        # Folium map display
        self.map_view = QWebEngineView()

        mainLayout.addLayout(leftLayout)
        mainLayout.addWidget(self.map_view)

        self.setLayout(mainLayout)

        self.setWindowTitle("Coordinate Logger")
        self.setGeometry(100, 100, 800, 600)
        self.show()

        self.newest = self.database.select_my_newest()
        # Initial map display
        self.updateMap(self.newest.x, self.newest.y)

    def updateCoordinates(self):
        logging.info("Updating Coords")

        gps = self.database.select_my_newest()
        if self.newest.id != gps.id:
            self.coordLabel.setText(f"Coordinates: (X: {gps.x}, Y: {gps.y})")
            # self.logArea.append(f"Updated Coordinates: (X: {gps.x}, Y: {gps.y})")
            self.updateMap(gps.x, gps.y)
            self.newest = gps

    def updateMap(self, latitude, longitude):
        # Create a Folium map
        folium_map = folium.Map(location=[latitude, longitude], zoom_start=80)
        folium.Marker([latitude, longitude], popup="Current Location").add_to(
            folium_map
        )

        map_file = "map.html"
        folium_map.save(map_file)

        html_map = QUrl.fromLocalFile(os.path.abspath(map_file))
        # Load the HTML into the QWebEngineView
        # self.map_view.setHtml(map_html)
        self.map_view.load(html_map)


def start(database, ip, port):
    app = QApplication(sys.argv)
    ex = CoordinateLogger(database, ip, port)
    sys.exit(app.exec_())
