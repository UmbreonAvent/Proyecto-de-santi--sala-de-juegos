from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import random
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Configuración de la conexión a MySQL
def conectar_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,             
        user="root",          
        password="Elpepe22/",
        database="sala_juegos",
        auth_plugin='mysql_native_password',
        use_pure=True
    )

# Función para enviar el correo electrónico
def enviar_correo_confirmacion(destinatario, nombre, apellido, fecha, hora, codigo):
    # CREDENCIALES INTEGRADAS
    remitente = "umbreonylio@gmail.com"
    password = "hwdlkyatltyuzzvd" # Contraseña de aplicación sin espacios

    msg = EmailMessage()
    msg['Subject'] = 'Confirmación de Reserva - Sala de Juegos'
    msg['From'] = remitente
    msg['To'] = destinatario

    # El mensaje exacto que pediste
    contenido = f"""Muy buenos dias
su reserva a nombre de {nombre} {apellido} se hizo con exito el {fecha} a las {hora}
su identificativo es {codigo}"""

    msg.set_content(contenido)

    try:
        # Configuración para el servidor de Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        print(f"Correo enviado exitosamente a {destinatario}")
    except Exception as e:
        print(f"Error enviando el correo: {e}")

# Ruta principal
@app.route('/')
def index():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    # Traemos también el código de reserva para mostrarlo en el panel
    consulta_reservas = """
        SELECT r.id_reserva, c.nombre AS cliente_nom, c.apellido AS cliente_ape, 
               j.nombre AS juego_nom, t.nombre AS trabajador_nom,
               r.fecha, r.hora, r.duracion, r.acompanado, r.codigo_reserva
        FROM reservas r
        JOIN clientes c ON r.dni_cliente = c.dni
        JOIN juegos j ON r.id_juego = j.id_juego
        JOIN trabajadores t ON r.id_trabajador = t.id_trabajador
    """
    cursor.execute(consulta_reservas)
    reservas = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    return render_template('index.html', clientes=clientes, reservas=reservas)


# Ruta para procesar el formulario de reserva
@app.route('/nueva_reserva', methods=['GET', 'POST'])
def nueva_reserva():
    if request.method == 'POST':
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        dni = request.form['dni']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo'] 
        fecha = request.form['fecha']
        hora = request.form['hora']
        duracion = request.form['duracion']
        acompanado = request.form['acompanado']
        juego = request.form['juego'] 
        
        trabajador_asignado = random.randint(1, 4)
        
        # Generar código aleatorio de 5 dígitos (ej: 48201)
        codigo_generado = str(random.randint(10000, 99999))
        
        # Registra o actualiza al cliente automáticamente, incluyendo el correo
        query_cliente = """
            INSERT INTO clientes (dni, nombre, apellido, correo) 
            VALUES (%s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), apellido=VALUES(apellido), correo=VALUES(correo)
        """
        cursor.execute(query_cliente, (dni, nombre, apellido, correo))
        
        # Guarda la reserva, incluyendo el código
        query_reserva = """
            INSERT INTO reservas (dni_cliente, id_juego, id_trabajador, fecha, hora, duracion, acompanado, codigo_reserva) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_reserva, (dni, juego, trabajador_asignado, fecha, hora, duracion, acompanado, codigo_generado))
        
        conexion.commit() 
        cursor.close()
        conexion.close()

        # Enviamos el correo justo después de guardar en la base de datos
        enviar_correo_confirmacion(correo, nombre, apellido, fecha, hora, codigo_generado)
        
        return redirect(url_for('index'))
        
    # --- CÓDIGO NUEVO PARA CARGAR LOS JUEGOS EN EL GET ---
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    # Suponiendo que la tabla se llama 'juegos' y las columnas son 'id_juego' y 'nombre'
    # Si la id de tus juegos se llama solo "id", cámbialo aquí abajo por "SELECT id as id_juego, nombre..."
    cursor.execute("SELECT id_juego, nombre FROM juegos")
    lista_juegos = cursor.fetchall()
    cursor.close()
    conexion.close()

    # Se le pasa la variable "juegos" a la plantilla HTML
    return render_template('nueva_reserva.html', juegos=lista_juegos)


if __name__ == '__main__':
    app.run(debug=True)