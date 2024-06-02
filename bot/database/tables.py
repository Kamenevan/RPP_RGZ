import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="RGZ",
    user="natasha",
    password="postgres"
)

with conn.cursor() as cur:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id SERIAL PRIMARY KEY,"
        "chat_id BIGINT NOT NULL,"
        "name VARCHAR(50) NOT NULL)"
    )

    cur.execute(
        "CREATE TABLE IF NOT EXISTS operations ("
        "id SERIAL PRIMARY KEY,"
        "date DATE NOT NULL,"
        "sum NUMERIC(15, 2) NOT NULL,"
        "chat_id BIGINT NOT NULL,"
        "type_operation VARCHAR(50) NOT NULL)"
    )
    conn.commit()
