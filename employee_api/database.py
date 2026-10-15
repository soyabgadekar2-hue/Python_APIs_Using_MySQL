import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))


def get_connection():
    required_settings = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing_settings = [
        setting for setting in required_settings if not os.getenv(setting)
    ]

    if missing_settings:
        missing_names = ", ".join(missing_settings)
        raise ValueError(f"Missing database settings: {missing_names}")

    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError:
        raise ValueError("DB_PORT must be a whole number.") from None

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=port,
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )