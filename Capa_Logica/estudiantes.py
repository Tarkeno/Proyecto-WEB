from Capa_Datos.conexion import conectar_bd

def obtener_estudiante_por_matricula(matricula):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        SELECT matricula, nombre, apellido_paterno, apellido_materno, carrera, semestre, grupo
        FROM estudiantes
        WHERE matricula = %s
    """, (matricula,))
    estudiante = cur.fetchone()
    cur.close()
    conn.close()
    return estudiante

