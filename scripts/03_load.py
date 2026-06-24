import os
import psycopg2
from dotenv import load_dotenv

# Environmental variables
load_dotenv()


def get_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        return connection
    except Exception as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None


def create_tables(conn):
    # ddl.sql's location
    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )  # BI-PORTFOLIO folder
    ddl_path = os.path.join(base_dir, "sql", "ddl.sql")
    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl = f.read()

    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("Tablas creadas (o ya existentes)")


def main():
    conn = get_connection()
    if conn is None:
        print("No se pudo establecer conexión")
        return
    print("Conectado a PostgreSQL")

    try:
        create_tables(conn)
    except Exception as e:
        print(f"\nError: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
