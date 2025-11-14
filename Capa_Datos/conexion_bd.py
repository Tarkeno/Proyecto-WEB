import psycopg2

def obtener_conexion():
    return psycopg2.connect(
        host="localhost",
        database="asistencias_bd",
        user="postgres",
        password="MiClave!2025"
    )
if __name__ == "__main__":
    conexion = obtener_conexion()
    print("Conexión exitosa a la base de datos")
    conexion.close()


