import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# Dependencias de voz e imagen (con fallbacks controlados)
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

DB_PATH = "productos.db"
IMG_PATH = "avatar_mujer.png"

# ========= VOZ (pyttsx3) =========
engine = None
def init_voice():
    global engine
    if pyttsx3 is None:
        return False
    try:
        engine = pyttsx3.init()
        # Intentar seleccionar una voz femenina en español si existe
        voices = engine.getProperty('voices') or []
        female_es = None
        female_any = None
        for v in voices:
            name_lang = f"{v.name} {getattr(v, 'languages', '')}"
            if ("es" in name_lang.lower() or "spanish" in name_lang.lower()) and ("female" in v.name.lower() or "mujer" in v.name.lower()):
                female_es = v
                break
            if ("female" in v.name.lower() or "mujer" in v.name.lower()):
                female_any = v
        if female_es:
            engine.setProperty('voice', female_es.id)
        elif female_any:
            engine.setProperty('voice', female_any.id)
        else:
            # Dejar la voz por defecto si no se encuentra femenina
            pass
        engine.setProperty('rate', 175)   # velocidad
        engine.setProperty('volume', 1.0) # volumen
        return True
    except Exception as e:
        print("Aviso: no se pudo inicializar la voz:", e)
        engine = None
        return False

def speak(text):
    if engine is None:
        return
    try:
        engine.stop()  # evitar solapamiento
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("Aviso: speak falló:", e)

voice_ready = init_voice()

# ========= BASE DE DATOS (SQLite) =========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        mayorista REAL,
        venta REAL
    )""")
    # Insertar más de 10 productos si está vacío
    cur.execute("SELECT COUNT(*) FROM productos")
    if cur.fetchone()[0] == 0:
        productos_iniciales = [
            ("Arroz 1kg", 3800, 5200),
            ("Aceite 1L", 7800, 9800),
            ("Azúcar 1kg", 3500, 4800),
            ("Sal 1kg", 2000, 3000),
            ("Leche 1L", 2500, 3500),
            ("Huevos docena", 8000, 11000),
            ("Pan 500g", 2500, 3500),
            ("Café 250g", 9000, 12000),
            ("Pasta 500g", 4000, 5500),
            ("Frijol 1kg", 4500, 6000),
            ("Harina 1kg", 3000, 4200)
        ]
        cur.executemany("INSERT INTO productos(nombre, mayorista, venta) VALUES (?,?,?)", productos_iniciales)
        conn.commit()
    return conn

conn = init_db()
cur = conn.cursor()

def upsert_producto(nombre, mayorista, venta):
    try:
        cur.execute("INSERT OR REPLACE INTO productos(nombre, mayorista, venta) VALUES (?,?,?)",
                    (nombre, float(mayorista), float(venta)))
        conn.commit()
        return True, "Producto guardado"
    except Exception as e:
        return False, f"Error al guardar: {e}"

def listar_productos():
    cur.execute("SELECT nombre, mayorista, venta FROM productos ORDER BY nombre")
    return cur.fetchall()

def buscar_precio(query_text):
    t = (query_text or "").lower().strip()
    if not t:
        return "Escribe o di el nombre del producto y si quieres 'mayorista' o 'venta'."
    # Buscar por coincidencia inclusiva simple
    productos = listar_productos()
    candidatos = []
    for nombre, mayorista, venta in productos:
        if nombre.lower() in t or nombre.split()[0].lower() in t:
            candidatos.append((nombre, mayorista, venta))
    if not candidatos:
        # Buscar por palabra clave individual
        palabras = t.split()
        for nombre, mayorista, venta in productos:
            for p in palabras:
                if p in nombre.lower():
                    candidatos.append((nombre, mayorista, venta))
                    break
    if not candidatos:
        return "No encontré ese producto. Revisa el nombre o agrégalo en el formulario."
    # Si hay múltiples, mostrar la primera coincidencia clara
    nombre, mayorista, venta = candidatos[0]
    if "mayorista" in t:
        return f"Mayorista de {nombre}: {mayorista:.0f} pesos."
    if "venta" in t or "precio" in t:
        return f"Precio de venta de {nombre}: {venta:.0f} pesos."
    return f"Precios de {nombre} • Mayorista: {mayorista:.0f} • Venta: {venta:.0f} pesos."

def promocion_10x100():
    cur.execute("SELECT nombre FROM productos ORDER BY nombre LIMIT 10")
    nombres = [r[0] for r in cur.fetchall()]
    if len(nombres) < 10:
        return "Aún no hay 10 productos para la promoción."
    return f"Promoción: 10 productos ({', '.join(nombres)}) por 100.000 pesos."

# ========= INTERFAZ (Tkinter) =========
root = tk.Tk()
root.title("Avatar de negocio • Texto + Voz (mujer) • Promociones")
root.geometry("900x600")
root.configure(bg="#0f1220")

# Layout principal
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=0)
root.rowconfigure(2, weight=0)
root.rowconfigure(3, weight=0)

# Panel Avatar (izquierda)
panel_avatar = tk.Frame(root, bg="#171a2a", bd=0)
panel_avatar.grid(row=0, column=0, rowspan=4, sticky="ns")
panel_avatar.configure(width=280)
for i in range(6):
    panel_avatar.rowconfigure(i, weight=0)

lbl_title = tk.Label(panel_avatar, text="Tu asistente", bg="#171a2a", fg="#e5e7eb", font=("Segoe UI", 12, "bold"))
lbl_title.grid(row=0, column=0, padx=12, pady=8)

# Imagen
img_label = tk.Label(panel_avatar, bg="#171a2a")
img_label.grid(row=1, column=0, padx=12, pady=8)
def load_image():
    if Image and ImageTk and os.path.exists(IMG_PATH):
        try:
            img = Image.open(IMG_PATH).resize((200,200))
            photo = ImageTk.PhotoImage(img)
            img_label.image = photo
            img_label.configure(image=photo)
        except Exception as e:
            img_label.configure(text="(No se pudo cargar la imagen)", fg="#ef4444")
    else:
        img_label.configure(text="(Imagen no disponible)", fg="#ef4444")
load_image()

# Estado de voz
voice_state = tk.StringVar(value=f"Voz: {'ON' if voice_ready else 'OFF'}")
btn_voice = tk.Button(panel_avatar, textvariable=voice_state, bg="#0ea56c", fg="#071b12", relief="raised",
                      command=lambda: toggle_voice())
btn_voice.grid(row=2, column=0, padx=12, pady=6)

def toggle_voice():
    global engine
    if engine:
        # Simular toggle desactivando engine temporalmente
        if voice_state.get().endswith("ON"):
            voice_state.set("Voz: OFF")
            # No hay API directa para OFF, usamos bandera por texto y evitamos speak en mostrar_respuesta si OFF
        else:
            voice_state.set("Voz: ON")
    else:
        # Reintentar inicializar voz si estaba OFF por fallo
        ok = init_voice()
        voice_state.set(f"Voz: {'ON' if ok else 'OFF'}")

# Panel Catálogo (arriba derecha)
panel_catalogo = tk.Frame(root, bg="#171a2a")
panel_catalogo.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
panel_catalogo.columnconfigure(0, weight=1)

tk.Label(panel_catalogo, text="Productos (Mayorista y Venta)", bg="#171a2a", fg="#9ca3af").grid(row=0, column=0, sticky="w")

frm_form = tk.Frame(panel_catalogo, bg="#171a2a")
frm_form.grid(row=1, column=0, sticky="ew", pady=6)
tk.Label(frm_form, text="Nombre", bg="#171a2a", fg="#e5e7eb").grid(row=0, column=0)
tk.Label(frm_form, text="Mayorista (COP)", bg="#171a2a", fg="#e5e7eb").grid(row=0, column=2)
tk.Label(frm_form, text="Venta (COP)", bg="#171a2a", fg="#e5e7eb").grid(row=0, column=4)

entry_nombre = tk.Entry(frm_form, width=28)
entry_mayorista = tk.Entry(frm_form, width=12)
entry_venta = tk.Entry(frm_form, width=12)
entry_nombre.grid(row=0, column=1, padx=6)
entry_mayorista.grid(row=0, column=3, padx=6)
entry_venta.grid(row=0, column=5, padx=6)

def on_guardar():
    nombre = entry_nombre.get().strip()
    mayorista = entry_mayorista.get().strip()
    venta = entry_venta.get().strip()
    if not nombre or not mayorista or not venta:
        messagebox.showwarning("Campos incompletos", "Completa nombre, mayorista y venta.")
        return
    try:
        float(mayorista); float(venta)
    except:
        messagebox.showwarning("Formato inválido", "Mayorista y Venta deben ser números.")
        return
    ok, msg = upsert_producto(nombre, mayorista, venta)
    if ok:
        entry_nombre.delete(0, tk.END)
        entry_mayorista.delete(0, tk.END)
        entry_venta.delete(0, tk.END)
        cargar_tabla()
    messagebox.showinfo("Estado", msg)

btn_guardar = tk.Button(frm_form, text="Guardar", command=on_guardar, bg="#12b981", fg="#071b12")
btn_guardar.grid(row=0, column=6, padx=6)

# Tabla
tabla = ttk.Treeview(panel_catalogo, columns=("Nombre","Mayorista","Venta"), show="headings", height=8)
tabla.heading("Nombre", text="Nombre")
tabla.heading("Mayorista", text="Mayorista")
tabla.heading("Venta", text="Venta")
tabla.grid(row=2, column=0, sticky="nsew", pady=6)

def cargar_tabla():
    for r in tabla.get_children():
        tabla.delete(r)
    for nombre, mayorista, venta in listar_productos():
        tabla.insert("", tk.END, values=(nombre, f"{mayorista:.0f}", f"{venta:.0f}"))

cargar_tabla()

# Panel Chat (medio derecha)
panel_chat = tk.Frame(root, bg="#171a2a")
panel_chat.grid(row=1, column=1, sticky="ew", padx=10)
tk.Label(panel_chat, text="Chat de precios", bg="#171a2a", fg="#9ca3af").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,6))

entry_pregunta = tk.Entry(panel_chat, width=50)
btn_preg_texto = tk.Button(panel_chat, text="Preguntar (texto)", bg="#131834", fg="#cbd5e1",
                           command=lambda: preguntar_texto())
btn_preg_voz = tk.Button(panel_chat, text="Preguntar (voz mujer)", bg="#131834", fg="#cbd5e1",
                         command=lambda: preguntar_voz())
btn_promo = tk.Button(panel_chat, text="Promoción 10x100mil", bg="#0ea56c", fg="#071b12",
                      command=lambda: mostrar_respuesta(promocion_10x100()))

entry_pregunta.grid(row=1, column=0, padx=6)
btn_preg_texto.grid(row=1, column=1, padx=6)
btn_preg_voz.grid(row=1, column=2, padx=6)
btn_promo.grid(row=1, column=3, padx=6)

# Respuesta
txt_resp = tk.Text(root, height=4, width=90, bg="#131834", fg="#e5e7eb")
txt_resp.grid(row=2, column=1, sticky="ew", padx=10, pady=8)
txt_resp.configure(state="disabled")

def mostrar_respuesta(texto):
    txt_resp.configure(state="normal")
    txt_resp.delete("1.0", tk.END)
    txt_resp.insert(tk.END, texto)
    txt_resp.configure(state="disabled")
    # Hablar solo si el botón está ON
    if voice_state.get().endswith("ON"):
        speak(texto)

def preguntar_texto():
    q = entry_pregunta.get().strip()
    if not q:
        mostrar_respuesta("Escribe tu pregunta (ej.: 'mayorista de arroz 1kg').")
        return
    mostrar_respuesta(buscar_precio(q))

def preguntar_voz():
    if sr is None:
        mostrar_respuesta("Reconocimiento de voz no disponible. Instala SpeechRecognition y PyAudio.")
        return
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            mostrar_respuesta("Te escucho... di el producto y si es mayorista o venta.")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        q = r.recognize_google(audio, language="es-ES")
        mostrar_respuesta(buscar_precio(q))
    except sr.WaitTimeoutError:
        mostrar_respuesta("No te escuché. Intenta de nuevo.")
    except sr.UnknownValueError:
        mostrar_respuesta("No entendí lo que dijiste.")
    except Exception as e:
        mostrar_respuesta(f"No pude usar el micrófono: {e}")

# Pie
tk.Label(root, text="Hecho con Tkinter + SQLite + Voz", bg="#0f1220", fg="#64748b").grid(row=3, column=1, sticky="e", padx=10, pady=6)

root.mainloop()