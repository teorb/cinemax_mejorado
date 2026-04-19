from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
import sys, os
import cloudinary
import cloudinary.uploader
import base64 as b64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import inicializar_db
from models.usuarios import login, registrar, email_existe
from models.peliculas import listar_peliculas, obtener_pelicula, crear_pelicula, editar_pelicula, eliminar_pelicula
from models.funciones import listar_funciones, obtener_funcion, crear_funcion, eliminar_funcion, asientos_funcion, ocupacion_funcion
from models.tiquetes import comprar_tiquete, obtener_tiquete, validar_tiquete, mis_tiquetes, reporte_ventas, peliculas_mas_vistas

app = Flask(__name__)
app.secret_key = "cine_secret_2024"

# ── MAIL CONFIG ───────────────────────────────────────────────────────────────
app.config['MAIL_SERVER']         = 'smtp.gmail.com'
app.config['MAIL_PORT']           = 587
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'noreply@cinemax.com')
mail = Mail(app)

# ── CLOUDINARY CONFIG ─────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key    = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

inicializar_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesion', 'error')
            return redirect(url_for('login_view'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash('Acceso solo para administradores', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login_view():
    if request.method == 'POST':
        u = login(request.form['email'], request.form['password'])
        if u:
            session['usuario_id'] = u['id']
            session['nombre']     = u['nombre']
            session['rol']        = u['rol']
            return redirect(url_for('admin_dashboard') if u['rol']=='admin' else url_for('index'))
        flash('Credenciales incorrectas', 'error')
    return render_template('login.html')

@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        nombre   = request.form['nombre']
        email    = request.form['email']
        password = request.form['password']
        if email_existe(email):
            flash('El correo ya esta registrado', 'error')
            return redirect(url_for('registro'))
        if registrar(nombre, email, password):
            flash('Registro exitoso. Inicia sesion', 'success')
            return redirect(url_for('login_view'))
        flash('Error al registrar', 'error')
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_view'))

# ── CARTELERA ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    peliculas = listar_peliculas()
    return render_template('index.html', peliculas=peliculas)

@app.route('/pelicula/<int:id>')
def detalle_pelicula(id):
    pelicula  = obtener_pelicula(id)
    funciones = listar_funciones(id)
    return render_template('detalle_pelicula.html', pelicula=pelicula, funciones=funciones)

# ── ASIENTOS Y COMPRA ─────────────────────────────────────────────────────────
@app.route('/funcion/<int:id>/asientos')
@login_required
def seleccionar_asientos(id):
    funcion  = obtener_funcion(id)
    asientos = asientos_funcion(id)
    filas    = {}
    for a in asientos:
        filas.setdefault(a['fila'], []).append(a)
    return render_template('asientos.html', funcion=funcion, filas=filas)

@app.route('/comprar', methods=['POST'])
@login_required
def comprar():
    funcion_id    = int(request.form['funcion_id'])
    asiento_ids   = request.form.getlist('asientos')
    email_destino = request.form.get('email_destino', '').strip()

    if not asiento_ids:
        flash('Selecciona al menos un asiento', 'error')
        return redirect(url_for('seleccionar_asientos', id=funcion_id))

    funcion     = obtener_funcion(funcion_id)
    asiento_ids = [int(a) for a in asiento_ids]
    codigo, error = comprar_tiquete(session['usuario_id'], funcion_id, asiento_ids, funcion['precio'])

    if error:
        flash(f'Error: {error}', 'error')
        return redirect(url_for('seleccionar_asientos', id=funcion_id))

    if email_destino:
        try:
            tiquete, asientos_det, qr_base64 = obtener_tiquete(codigo)
            asientos_str = ', '.join(f"{a['fila']}{a['columna']}" for a in asientos_det)

            upload_result = cloudinary.uploader.upload(
                f"data:image/png;base64,{qr_base64}",
                public_id=f"qr_{codigo}",
                overwrite=True
            )
            qr_url = upload_result['secure_url']

            html_correo = render_template('email_factura.html',
                tiquete=tiquete, asientos=asientos_det,
                asientos_str=asientos_str,
                qr_url=qr_url,
                nombre_usuario=session.get('nombre', ''))

            msg = Message(
                subject=f'🎬 Tu tiquete CINE MAX – {tiquete["titulo"]}',
                recipients=[email_destino],
                html=html_correo
            )
            mail.send(msg)
            flash('¡Compra exitosa! Te enviamos tu tiquete por correo.', 'success')
        except Exception as e:
            flash(f'Compra exitosa, pero no se pudo enviar el correo: {e}', 'error')
    else:
        flash('¡Compra exitosa!', 'success')

    return redirect(url_for('ver_tiquete', codigo=codigo))

@app.route('/tiquete/<codigo>')
@login_required
def ver_tiquete(codigo):
    tiquete, asientos, qr_base64 = obtener_tiquete(codigo)
    return render_template('tiquete.html', tiquete=tiquete, asientos=asientos, qr_base64=qr_base64)

@app.route('/mis-tiquetes')
@login_required
def mis_tiquetes_view():
    tiquetes = mis_tiquetes(session['usuario_id'])
    return render_template('mis_tiquetes.html', tiquetes=tiquetes)

# ── VALIDACION ────────────────────────────────────────────────────────────────
@app.route('/validar', methods=['GET','POST'])
@login_required
def validar():
    resultado = None
    if request.method == 'POST':
        codigo = request.form['codigo'].strip().upper()
        tiquete, msg = validar_tiquete(codigo)
        resultado = {'tiquete': tiquete, 'msg': msg}
    return render_template('validar.html', resultado=resultado)

# ── ADMIN ─────────────────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    peliculas      = listar_peliculas(solo_activas=False)
    funciones      = listar_funciones()
    ventas         = reporte_ventas()
    mas_vistas     = peliculas_mas_vistas()
    total_ingresos = sum(v['ingresos'] or 0 for v in ventas)
    total_tiquetes = sum(v['tiquetes'] or 0 for v in ventas)
    return render_template('admin/dashboard.html',
        peliculas=peliculas, funciones=funciones, ventas=ventas,
        mas_vistas=mas_vistas,
        total_ingresos=total_ingresos, total_tiquetes=total_tiquetes)

@app.route('/admin/pelicula/nueva', methods=['GET','POST'])
@login_required
@admin_required
def nueva_pelicula():
    if request.method == 'POST':
        crear_pelicula(request.form['titulo'], request.form['descripcion'],
            request.form['duracion'], request.form['genero'],
            request.form['clasificacion'], request.form['imagen_url'])
        flash('Pelicula creada', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/pelicula_form.html', pelicula=None)

@app.route('/admin/pelicula/editar/<int:id>', methods=['GET','POST'])
@login_required
@admin_required
def editar_pelicula_view(id):
    pelicula = obtener_pelicula(id)
    if request.method == 'POST':
        editar_pelicula(id, request.form['titulo'], request.form['descripcion'],
            request.form['duracion'], request.form['genero'],
            request.form['clasificacion'], request.form['imagen_url'],
            request.form['estado'])
        flash('Pelicula actualizada', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/pelicula_form.html', pelicula=pelicula)

@app.route('/admin/pelicula/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_pelicula_view(id):
    eliminar_pelicula(id)
    flash('Pelicula eliminada', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/funcion/nueva', methods=['GET','POST'])
@login_required
@admin_required
def nueva_funcion():
    peliculas = listar_peliculas(solo_activas=False)
    if request.method == 'POST':
        ok, msg = crear_funcion(request.form['pelicula_id'], request.form['fecha'],
            request.form['hora'], request.form['precio'])
        if ok:
            flash(msg, 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(msg, 'error')
            return render_template('admin/funcion_form.html', peliculas=peliculas)
    return render_template('admin/funcion_form.html', peliculas=peliculas)

@app.route('/admin/funcion/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_funcion_view(id):
    eliminar_funcion(id)
    flash('Funcion eliminada', 'success')
    return redirect(url_for('admin_dashboard'))

# ── RECUPERAR CONTRASEÑA ──────────────────────────────────────────────────────
@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    paso = 1
    email_verificado = None
    mensaje = None

    if request.method == 'POST':
        if 'email' in request.form and 'nueva_password' not in request.form:
            email = request.form['email'].strip()
            if email_existe(email):
                paso = 2
                email_verificado = email
            else:
                mensaje = 'No existe una cuenta con ese correo'
                paso = 1

        elif 'nueva_password' in request.form:
            email = request.form['email'].strip()
            nueva = request.form['nueva_password'].strip()
            confirmar = request.form['confirmar_password'].strip()
            if nueva != confirmar:
                mensaje = 'Las contraseñas no coinciden'
                paso = 2
                email_verificado = email
            else:
                from database import get_connection
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE usuarios SET password=%s WHERE email=%s", (nueva, email))
                conn.commit()
                conn.close()
                flash('Contraseña actualizada. Inicia sesión.', 'success')
                return redirect(url_for('login_view'))

    return render_template('recuperar.html', paso=paso,
                           email_verificado=email_verificado, mensaje=mensaje)

if __name__ == '__main__':
    app.run(debug=True)
