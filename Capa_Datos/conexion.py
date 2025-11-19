import psycopg2

def conectar_bd():
    return psycopg2.connect(
        host="localhost",
        database="db_control",
        user="postgres",
        password="12345"
    )

