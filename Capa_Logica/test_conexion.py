from Capa_Datos.conexion import conectar_bd

try:
    conn = conectar_bd()
    print("Conexión exitosa")
    conn.close()
except Exception as e:
    print("Error al conectar:", e)