#!/usr/bin/python3
import time
import atexit
import logging
import threading
from datetime import datetime
from queue import Queue as NewQueue
from pypika import PostgreSQLQuery as Query, Schema, Column
import register
from config import config
from classes import Request, Response
from interceptors.database import DatabaseConnection


schemaname = config.get('logging', 'schema') if config.has_option('logging', 'schema') else 'interceptor'
tablename = config.get('logging', 'logging_table') if config.has_option('logging', 'logging_table') else 'audit_log'

queue = NewQueue()


@register.teardown_request
def log(request: Request, response: Response):
    queue.put(dict(
        timestamp=datetime.now(),
        client=request.client,
        path=request.path,
        method=request.method,
        user=request.headers.get("x-user"),
        response_code=response.status,
    ))


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
        logging.info(f"Table {schemaname}.{tablename} was created")


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
    while app_alive:
        try:
            log_queue()
        except Exception as exc:
            print(f"Failed to write log to queue: {type(exc).__name__}: {exc}")
        for _ in range(5):
            if not app_alive:
                break
            time.sleep(1)


@atexit.register
def set_dead():
    global app_alive
    app_alive = False


app_alive = True
atexit.register(log_queue)
create_tables()
worker_thread = threading.Thread(target=logger_worker, name="logging-worker", daemon=True)
worker_thread.start()
