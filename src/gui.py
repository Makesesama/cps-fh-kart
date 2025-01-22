import sys
import serial
import time
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QGridLayout,
)
from PyQt5.QtCore import QTimer


class TemperatureMeasurementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)  # Timer for updating the temperature

    def initUI(self):
        # Create layout
        layout = QGridLayout()

    def param_measurement(self):
        # Placeholder function for parameterizing the measurement
        sample_rate = self.line_edit_sample_rate.text()
        unit = self.combo_box_unit.currentText()
        print(f"Parameters set: Sampling rate - {sample_rate} ms, Unit - {unit}")
        # Set the sampling time for the timer
        self.timer.setInterval(int(sample_rate))

    def start_measurement(self):
        # Start reading data from the sensor periodically
        self.timer.timeout.connect(self.current_point)
        self.timer.start()

    def stop_measurement(self):
        print("Measurement stopped.")

    def current_point(self):
        self.update_point_display(1.24)

    def update_point_display(self, temp_data):
        # Update the temperature field based on the unit selected
        unit = self.combo_box_unit.currentText()
        temp_value = float(temp_data)

        self.line_edit_current_temp.setText(
            f"{temp_value:.2f} {unit[: unit.index('[')].strip()}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TemperatureMeasurementApp()
    ex.show()
    sys.exit(app.exec_())
