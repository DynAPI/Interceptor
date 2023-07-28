#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import psycopg2 as psql
import psycopg2.extras
from config import config


class DatabaseConnection:
    conn: psql.extras.NamedTupleConnection = None

    def __init__(self):
        self.conn = psql.connect(
            database=config.get("database", "database"),
            user=config.get("database", "user"),
            password=config.get("database", "password"),
            host=config.get("database", "host", fallback="localhost"),
            port=config.getint("database", "port", fallback=5432),
            connect_timeout=config.getint("database", "connect_timeout", fallback=5),
            connection_factory=psql.extras.NamedTupleConnection,
        )

    def __del__(self):
        if getattr(self, 'conn') and not self.conn.closed:
            self.conn.close()

    close = __del__

    def __enter__(self):
        self.conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.__exit__(exc_type, exc_val, exc_tb)

    def cursor(self) -> psql.extras.NamedTupleCursor:
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()
