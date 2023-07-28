from config import config
from pypika import PostgreSQLQuery as Query, Schema
from interceptors.database import DatabaseConnection


schemaname = config.get('auth', 'schema') if config.has_option('auth', 'schema') else 'interceptor'
tablename = config.get('auth', 'users_table') if config.has_option('auth', 'users_table') else 'users'
def create_users_table():
    from pypika import Column

    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        query = Query \
            .create_table(Schema(schemaname).__getattr__(tablename)) \
            .columns(
                Column("username", "VARCHAR", nullable=False),
                Column("passwordhash", "VARCHAR", nullable=False),
                Column("description", "VARCHAR", nullable=False),
                Column("roles", "VARCHAR[]", nullable=True)) \
            .unique("username") \
            .primary_key("username") \
            .if_not_exists()

        cursor.execute(str(query))
        conn.commit()

create_users_table()