#!/usr/bin/python3
import time
from queue import Queue as NewQueue
import atexit
import threading
import typing as t
from datetime import datetime
from pypika import PostgreSQLQuery as Query, Schema, Column
from interceptors.database import DatabaseConnection
from src.interceptor.config import config
from classes import Request, Response


schemaname = config.get('logging', 'schema') if config.has_option('logging', 'schema') else 'interceptor'
tablename = config.get('logging', 'logging_table') if config.has_option('logging', 'logging_table') else 'audit_log'

queue = NewQueue()

def log(request: Request, response: Response):
    try:
        log: t.Dict[str, t.Any] = {}
        log["timestamp"] = datetime.now()
        log["client"] = request.client
        log["path"] = request.path
        log["method"] = request.method
        log["user"] = request.headers.get("x-user")
        log["response_code_protected_api"] = response.status
        queue.put(log)
    except Exception as exc:
        print(f"Failed to write log to queue: {type(exc).__name__}: {exc}")


def create_tables():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        query = Query \
            .create_table(Schema(schemaname).__getattr__(tablename)) \
            .columns(
                Column("id", "SERIAL", nullable=False),
                Column("client", "VARCHAR", nullable=False),
                Column("user", "VARCHAR", nullable=True),
                Column("method", "VARCHAR", nullable=False),
                Column("path", "VARCHAR", nullable=False),
                Column("response_code", "SMALLINT", nullable=False),
                Column("timestamp", "TIMESTAMP", nullable=False))\
            .unique("id") \
            .primary_key("id") \
            .if_not_exists()
        cursor.execute(str(query))
        conn.commit()


def log_queue():
    if queue.empty():
        return
    print(f"insert {queue.qsize()} logs into database")
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        schema = Schema(schemaname)
        query = Query.into(schema.__getattr__(tablename)) \
            .columns("client", "user", "method", "path", "response_code", "timestamp")

        while not queue.empty():
            log = queue.get()
            query = query.insert(log.get("client"), log.get("user"), log.get("method"), log.get("path"), log.get("response_code"), log.get("timestamp"))
            queue.task_done()

        cursor.execute(str(query))
        conn.commit()


def logger_worker():
    while app.alive:  # noqa
        try:
            log_queue()
        except Exception as exc:
            print(f"Failed to write log to queue: {type(exc).__name__}: {exc}")
        for _ in range(15):
            if not app.alive:  # noqa
                break
            time.sleep(1)


atexit.register(log_queue)
create_tables()
worker_thread = threading.Thread(target=logger_worker, name="logging-worker", daemon=True)
worker_thread.start()