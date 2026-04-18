from database import get_connection
import random, string, qrcode, base64
from io import BytesIO

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def generar_qr_base64(codigo):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(codigo)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a56db", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def comprar_tiquete(usuario_id, funcion_id, asiento_ids, precio_unitario):
    conn = get_connection()
    cur = conn.cursor()
    try:
        for asiento_id in asiento_ids:
            cur.execute("SELECT estado FROM asiento_funcion WHERE funcion_id=? AND asiento_id=?",
                (funcion_id, asiento_id))
            r = cur.fetchone()
            if not r or (r['estado'] if hasattr(r,'keys') else r[0]) != 'disponible':
                conn.close()
                return None, "El asiento ya esta ocupado"

        codigo = generar_codigo()
        total  = len(asiento_ids) * precio_unitario

        cur.execute("INSERT INTO tiquetes (codigo, usuario_id, funcion_id, total) VALUES (?,?,?,?)",
            (codigo, usuario_id, funcion_id, total))
        tiquete_id = cur.lastrowid

        for asiento_id in asiento_ids:
            cur.execute("INSERT INTO detalle_tiquete (tiquete_id, asiento_id, precio_unitario) VALUES (?,?,?)",
                (tiquete_id, asiento_id, precio_unitario))
            cur.execute("UPDATE asiento_funcion SET estado='ocupado' WHERE funcion_id=? AND asiento_id=?",
                (funcion_id, asiento_id))

        conn.commit()
        conn.close()
        return codigo, None
    except Exception as e:
        conn.close()
        return None, str(e)

def obtener_tiquete(codigo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT t.*, f.fecha, f.hora, f.precio, p.titulo, p.imagen_url,
        u.nombre as usuario_nombre
        FROM tiquetes t
        JOIN funciones f ON t.funcion_id=f.id
        JOIN peliculas p ON f.pelicula_id=p.id
        LEFT JOIN usuarios u ON t.usuario_id=u.id
        WHERE t.codigo=?""", (codigo,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None, [], None
    tiquete = dict(row)
    cur.execute("""SELECT a.fila, a.columna FROM detalle_tiquete dt
        JOIN asientos a ON dt.asiento_id=a.id
        WHERE dt.tiquete_id=?""", (tiquete['id'],))
    asientos = [dict(r) for r in cur.fetchall()]
    conn.close()
    qr_base64 = generar_qr_base64(codigo)
    return tiquete, asientos, qr_base64

def validar_tiquete(codigo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tiquetes WHERE codigo=?", (codigo,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None, "Tiquete no encontrado"
    t = dict(row)
    if t['estado'] == 'usado':
        conn.close()
        return t, "Ya fue usado"
    if t['estado'] == 'cancelado':
        conn.close()
        return t, "Tiquete cancelado"
    cur.execute("UPDATE tiquetes SET estado='usado' WHERE codigo=?", (codigo,))
    conn.commit()
    conn.close()
    return t, "Valido"

def mis_tiquetes(usuario_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT t.*, p.titulo, f.fecha, f.hora
        FROM tiquetes t
        JOIN funciones f ON t.funcion_id=f.id
        JOIN peliculas p ON f.pelicula_id=p.id
        WHERE t.usuario_id=?
        ORDER BY t.fecha_compra DESC""", (usuario_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def reporte_ventas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT p.titulo, COUNT(t.id) as tiquetes, SUM(t.total) as ingresos
        FROM tiquetes t
        JOIN funciones f ON t.funcion_id=f.id
        JOIN peliculas p ON f.pelicula_id=p.id
        WHERE t.estado != 'cancelado'
        GROUP BY p.titulo ORDER BY ingresos DESC""")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def peliculas_mas_vistas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT p.titulo, p.imagen_url, p.genero,
        COUNT(DISTINCT t.id) as total_tiquetes,
        COUNT(DISTINCT dt.asiento_id) as total_asientos,
        SUM(t.total) as ingresos
        FROM peliculas p
        LEFT JOIN funciones f ON p.id = f.pelicula_id
        LEFT JOIN tiquetes t ON f.id = t.funcion_id AND t.estado != 'cancelado'
        LEFT JOIN detalle_tiquete dt ON t.id = dt.tiquete_id
        GROUP BY p.id
        ORDER BY total_asientos DESC""")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
