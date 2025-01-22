import os


def get_config_option(config_name: str):
    default_values = {
        "PORT": 8000,
        "TARGET_HOST": "localhost",
        "DB_PATH": "./sqlite3.db",
    }
    return os.environ.get(config_name, default_values[config_name])
