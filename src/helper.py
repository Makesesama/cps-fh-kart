import os
import socket
from xdg import BaseDirectory

local_path = BaseDirectory.save_data_path("cps_fh_kart")
sleep_time = 5


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


my_ip = get_ip_address()


def get_config_option(config_name: str):
    default_values = {
        "PORT": 43840,
        "TARGET_HOST": "192.168.100.120",
        "DB_PATH": f"{local_path}/sqlite3.db",
    }
    return os.environ.get(config_name, default_values[config_name])
