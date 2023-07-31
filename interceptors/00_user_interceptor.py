#!/usr/bin/python3
import register
from classes import Request


@register.before_request
def check_api_key(request: Request):
    authorization = request.authorization
    if authorization is None:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, "missing authorization header")
    user = request.headers.get("x-user")
    if user is None:
        request.headers.add_header("x-user", authorization.username)
    else:
        request.headers.replace_header("x-user", f"{user}/{authorization.username}")

    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        table = Table(tablename)
        query = Query \
            .from_(Schema(schemaname).__getattr__(tablename)) \
            .select('*') \
            .where(table.username == authorization.username)
        cursor.execute(str(query))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(HTTPStatus.UNAUTHORIZED)
        if not compare_password_to_hash(authorization.password.encode(), base64.b64decode(row.passwordhash.encode())):
            raise HTTPException(HTTPStatus.UNAUTHORIZED)

        if not method_check(method=request.method, path=request.path, roles=tuple(row.roles)):
            raise HTTPException(HTTPStatus.FORBIDDEN)


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
        logging.info(f"Table {schemaname}.{tablename} was created")


def compare_password_to_hash(pw: bytes, hsh: bytes) -> bool:
    salt, pwhashed = hsh[:32], hsh[32:]
    hashed = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=pw,
        salt=salt,
        iterations=100_000,
    )
    return hmac.compare_digest(pwhashed, hashed)


create_users_table()
