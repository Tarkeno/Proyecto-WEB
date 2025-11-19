from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

# Conexión a la base de datos
def conectar_bd():
    return psycopg2.connect(
        host="localhost",
        database="db_control",
        user="postgres",
        password="12345"
    )


@app.route("/api/modificar-reporte")
def modificar_reporte():
    matricula = request.args.get("matricula")
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not matricula or not inicio or not fin:
        return jsonify({"error": "Faltan parámetros"}), 400

    conn = conectar_bd()   # tu configuración de conexión
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.matricula, e.nombre, e.apellido_paterno, e.apellido_materno,
               e.carrera, e.semestre, e.grupo, a.fecha, a.estado_asistencia
        FROM asistencias a
        JOIN estudiantes e ON a.matricula = e.matricula
        WHERE a.matricula = %s AND a.fecha >= %s AND a.fecha < %s::date + INTERVAL '1 day'
        ORDER BY a.fecha
    """, (matricula, inicio, fin))

    resultados = cursor.fetchall()
    registros = []

    for r in resultados:
        registros.append({
            "matricula": r[0],
            "nombre": r[1],
            "apellido_paterno": r[2],
            "apellido_materno": r[3],
            "carrera": r[4],
            "semestre": r[5],
            "grupo": r[6],
            "fecha": r[7].strftime("%Y-%m-%d"),
            "estado_asistencia": r[8]  # ← ahora sí es estado_asistencia
        })

    cursor.close()
    conn.close()
    return jsonify(registros)
@app.route('/buscar_estudiante', methods=['POST'])
def buscar_estudiante():
    data = request.get_json()
    matricula = data.get("matricula")

    if not matricula:
        return jsonify({"error": "Matrícula no proporcionada"}), 400

    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("""
        SELECT matricula, nombre, apellido_paterno, apellido_materno,
               carrera, semestre, grupo
        FROM estudiantes
        WHERE matricula = %s
    """, (matricula,))

    estudiante = cur.fetchone()
    cur.close()
    conn.close()

    if estudiante:
        return jsonify({
            "matricula": estudiante[0],
            "nombre": estudiante[1],
            "apellido_paterno": estudiante[2],
            "apellido_materno": estudiante[3],
            "carrera": estudiante[4],
            "semestre": estudiante[5],
            "grupo": estudiante[6]
        })
    else:
        return jsonify({"error": "Estudiante no encontrado"}), 404


# 💾 Guardar cambios en el estado
@app.route('/api/guardar-cambios', methods=['POST'])
def guardar_cambios():
    data = request.get_json()
    cambios = data.get("cambios", [])

    if not cambios:
        return jsonify({"mensaje": "No se recibieron cambios."}), 400

    conn = conectar_bd()
    cur = conn.cursor()

    for cambio in cambios:
        matricula = cambio["matricula"]
        fecha = cambio["fecha"]
        estado = cambio["estado_asistencia"]

        cur.execute("""
            UPDATE asistencias
            SET estado_asistencia = %s
            WHERE matricula = %s AND fecha = %s
        """, (estado, matricula, fecha))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensaje": "Cambios guardados correctamente."})

# 🗑️ Eliminar un registro
@app.route('/api/eliminar-registro', methods=['POST'])
def eliminar_registro():
    data = request.get_json()
    matricula = data.get("matricula")
    fecha = data.get("fecha")

    if not matricula or not fecha:
        return jsonify({"error": "Faltan datos"}), 400

    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM asistencias
        WHERE matricula = %s AND fecha = %s
    """, (matricula, fecha))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"mensaje": "Registro eliminado correctamente."})

@app.route("/api/reporte")
def generar_reporte_general():
    tipo = request.args.get("tipo")
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")
    matricula = request.args.get("matricula")  # opcional

    if not tipo or not inicio or not fin:
        return jsonify({"error": "Faltan parámetros"}), 400

    conn = conectar_bd()
    cursor = conn.cursor()

    if tipo == "general":
        query = """
            SELECT a.matricula, e.nombre, e.apellido_paterno, e.apellido_materno,
                   e.carrera, e.semestre, e.grupo,
                   COUNT(CASE WHEN a.estado_asistencia = 'Asistencia' THEN 1 END) AS asistencias,
                   COUNT(CASE WHEN a.estado_asistencia = 'Inasistencia' THEN 1 END) AS inasistencias,
                   COUNT(CASE WHEN a.estado_asistencia = 'Justificación' THEN 1 END) AS justificaciones
            FROM asistencias a
            JOIN estudiantes e ON a.matricula = e.matricula
            WHERE a.fecha >= %s AND a.fecha < %s::date + INTERVAL '1 day'
        """
        params = [inicio, fin]
        if matricula:
            query += " AND a.matricula = %s"
            params.append(matricula)
        query += " GROUP BY a.matricula, e.nombre, e.apellido_paterno, e.apellido_materno, e.carrera, e.semestre, e.grupo ORDER BY e.nombre"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        registros = [{
            "matricula": r[0],
            "nombre": r[1],
            "apellido_paterno": r[2],
            "apellido_materno": r[3],
            "carrera": r[4],
            "semestre": r[5],
            "grupo": r[6],
            "asistencias": r[7],
            "inasistencias": r[8],
            "justificaciones": r[9]
        } for r in resultados]

    elif tipo in ["asistencias", "inasistencias", "justificaciones"]:
        estado = {
            "asistencias": "Asistencia",
            "inasistencias": "Inasistencia",
            "justificaciones": "Justificación"
        }[tipo]

        query = """
            SELECT a.matricula, e.nombre, e.apellido_paterno, e.apellido_materno,
                   e.carrera, e.semestre, e.grupo, a.fecha
            FROM asistencias a
            JOIN estudiantes e ON a.matricula = e.matricula
            WHERE a.estado_asistencia = %s
              AND a.fecha >= %s AND a.fecha < %s::date + INTERVAL '1 day'
        """
        params = [estado, inicio, fin]
        if matricula:
            query += " AND a.matricula = %s"
            params.append(matricula)
        query += " ORDER BY a.fecha"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        registros = [{
            "matricula": r[0],
            "nombre": r[1],
            "apellido_paterno": r[2],
            "apellido_materno": r[3],
            "carrera": r[4],
            "semestre": r[5],
            "grupo": r[6],
            "fecha": r[7].strftime("%Y-%m-%d")
        } for r in resultados]

    else:
        cursor.close()
        conn.close()
        return jsonify({"error": "Tipo de reporte no soportado"}), 400

    cursor.close()
    conn.close()
    return jsonify(registros)

@app.route('/api/agregar_estudiante', methods=['POST'])
def agregar_estudiante():
    data = request.get_json()

    matricula = data.get("matricula")
    nombre = data.get("nombre")
    apellido_paterno = data.get("apellido_paterno")
    apellido_materno = data.get("apellido_materno")
    carrera = data.get("carrera")
    semestre = data.get("semestre")
    grupo = data.get("grupo")

    if not all([matricula, nombre, apellido_paterno, apellido_materno, carrera, semestre, grupo]):
        return jsonify({"success": False, "message": "Faltan datos obligatorios"}), 400

    try:
        conn = conectar_bd()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO estudiantes (matricula, nombre, apellido_paterno, apellido_materno, carrera, semestre, grupo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (matricula, nombre, apellido_paterno, apellido_materno, carrera, semestre, grupo))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Estudiante agregado correctamente"})
    except Exception as e:
        print("Error al insertar estudiante:", e)
        return jsonify({"success": False, "message": "Error al insertar en la base de datos"}), 500
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario = data.get("usuario")
    contraseña = data.get("contraseña")

    if not usuario or not contraseña:
        return jsonify({"success": False, "message": "Faltan credenciales"}), 400

    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre, apellido_paterno, apellido_materno, rol, es_maestro
        FROM usuarios
        WHERE usuario = %s AND contraseña = %s
    """, (usuario, contraseña))

    resultado = cur.fetchone()
    cur.close()
    conn.close()

    if resultado:
        return jsonify({
            "success": True,
            "usuario": usuario,
            "rol": resultado[4],
            "es_maestro": resultado[5]
        })
    else:
        return jsonify({"success": False, "message": "Credenciales incorrectas"})
@app.route('/api/registrar_usuario', methods=['POST'])
def registrar_usuario():
    data = request.get_json()

    nombre = data.get("nombre")
    apellido_paterno = data.get("apellido_paterno")
    apellido_materno = data.get("apellido_materno")
    usuario = data.get("usuario")
    contraseña = data.get("contraseña")
    rol = data.get("rol")
    es_maestro = data.get("es_maestro", False)

    if not all([nombre, apellido_paterno, apellido_materno, usuario, contraseña, rol]):
        return jsonify({"success": False, "message": "Faltan datos obligatorios"}), 400

    try:
        conn = conectar_bd()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO usuarios (nombre, apellido_paterno, apellido_materno, usuario, contraseña, rol, es_maestro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido_paterno, apellido_materno, usuario, contraseña, rol, es_maestro))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Usuario registrado correctamente"})
    except Exception as e:
        print("Error al registrar usuario:", e)
        return jsonify({"success": False, "message": "Error al insertar en la base de datos"}), 500

# 🚀 Ejecutar la app
if __name__ == '__main__':
    app.run(debug=True)