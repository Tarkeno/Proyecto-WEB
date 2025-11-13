from flask import Flask, request, jsonify
from Capa_Datos.conexion_bd import obtener_conexion
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "../Capa_Presentacion/static"))

app = Flask(__name__, static_folder=STATIC_FOLDER)

@app.route('/')
def home():
    return app.send_static_file('Html/login.html')



# Endpoint opcional para depurar y ver archivos realmente disponibles
@app.route('/listar')
def listar():
    archivos = os.listdir(app.static_folder)
    return "<br>".join(archivos)

@app.route('/api/estudiantes', methods=['GET'])
def consultar_estudiantes():
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Alumno;")
    datos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(datos)

@app.route('/api/estudiante', methods=['POST'])
def info_estudiante():
    data = request.get_json()
    print("POST recibido:", data)
    matricula = data.get("Matricula") or data.get("matricula")
    if not matricula:
        return jsonify({"error": "No se recibió matrícula"}), 400
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("SELECT Matricula, Codigo_QR, Nombre, Apellido_Paterno, Apellido_Materno, Semestre, Carrera, Id_Grupo FROM Alumno WHERE Matricula=%s;", (matricula,))
    datos = cur.fetchone()
    cur.close()
    conn.close()
    if datos:
        keys = ['Matricula', 'Codigo_QR', 'Nombre', 'Apellido_Paterno', 'Apellido_Materno', 'Semestre', 'Carrera', 'Id_Grupo']
        return jsonify(dict(zip(keys, datos)))
    else:
        return jsonify({"error": "No encontrado"}), 404

@app.route('/api/estudiante', methods=['PUT'])
def actualizar_estudiante():
    data = request.get_json()
    # Recupera los campos de data...
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("UPDATE alumnos SET nombre=%s, apellido_paterno=%s, apellido_materno=%s, carrera=%s, semestre=%s, grupo=%s WHERE matricula=%s;",
                (data['nombre'], data['apellido_paterno'], data['apellido_materno'], data['carrera'], data['semestre'], data['grupo'], data['matricula']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Actualizado correctamente"})

@app.route('/api/estudiante', methods=['DELETE'])
def eliminar_estudiante():
    data = request.get_json()
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM alumnos WHERE matricula=%s;", (data['matricula'],))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Eliminado correctamente"})

@app.route('/api/estudiante', methods=['POST'])
def insertar_estudiante():
    data = request.get_json()
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("INSERT INTO alumnos (matricula, qr, nombre, apellido_paterno, apellido_materno, semestre, carrera, grupo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);",
                (data['matricula'], data['qr'], data['nombre'], data['apellido_paterno'], data['apellido_materno'], data['semestre'], data['carrera'], data['grupo']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Insertado correctamente"})

if __name__ == '__main__':
    app.run(debug=True)
