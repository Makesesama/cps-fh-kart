import os
from xdg import BaseDirectory

local_path = BaseDirectory.save_data_path("cps_fh_kart")


def get_config_option(config_name: str):
    default_values = {
        "PORT": 43840,
        "TARGET_HOST": "localhost",
        "DB_PATH": f"{local_path}/sqlite3.db",
    }
    return os.environ.get(config_name, default_values[config_name])
