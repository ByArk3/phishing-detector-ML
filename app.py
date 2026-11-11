import html
import re
import joblib
import pandas as pd
import streamlit as st
from procesamiento import limpiar_texto, estructurales, URGENCIA

st.set_page_config(page_title="Detector de phishing", layout="centered")

@st.cache_resource
def cargar_modelo():
    return joblib.load("modelo_phishing.joblib")

modelo = cargar_modelo()

# modo día / noche (se guarda mientras la página esté abierta)
if "oscuro" not in st.session_state:
    st.session_state.oscuro = st.context.theme.type == "dark"

def cambiar_modo():
    st.session_state.oscuro = not st.session_state.oscuro

# colores de cada modo
if st.session_state.oscuro:
    c = {"fondo": "radial-gradient(circle at 15% 0%, #1E1B4B 0%, #0B1120 45%)",
         "fondo2": "linear-gradient(180deg, #111A2E 0%, #0B1120 100%)",
         "tarjeta": "#16213A", "borde": "#26324D", "sombra": "rgba(0,0,0,0.45)",
         "texto": "#E2E8F0", "suave": "#94A3B8", "principal": "#60A5FA", "texto_boton": "#0B1120",
         "brillo": "rgba(96,165,250,0.35)",
         "banner": "linear-gradient(120deg, #1E3A8A, #5B21B6, #1E3A8A)",
         "rojo": "#F87171", "rojo_fondo": "rgba(248,113,113,0.12)",
         "verde": "#4ADE80", "verde_fondo": "rgba(74,222,128,0.12)"}
else:
    c = {"fondo": "radial-gradient(circle at 15% 0%, #E0E7FF 0%, #F5F7FF 40%, #FFFFFF 100%)",
         "fondo2": "linear-gradient(180deg, #EEF2FF 0%, #FFFFFF 100%)",
         "tarjeta": "#FFFFFF", "borde": "#E0E7FF", "sombra": "rgba(30,64,175,0.10)",
         "texto": "#0F172A", "suave": "#64748B", "principal": "#1D4ED8", "texto_boton": "#FFFFFF",
         "brillo": "rgba(29,78,216,0.25)",
         "banner": "linear-gradient(120deg, #1D4ED8, #7C3AED, #1D4ED8)",
         "rojo": "#B91C1C", "rojo_fondo": "#FEF2F2",
         "verde": "#15803D", "verde_fondo": "#F0FDF4"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
.stApp {{ background: {c["fondo"]}; }}
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3 {{
    color: {c["texto"]}; font-family: 'Poppins', sans-serif; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: {c["fondo2"]}; border-right: 1px solid {c["borde"]}; }}

/* cuadro de texto: se ilumina al escribir */
.stApp textarea {{ background: {c["tarjeta"]} !important; color: {c["texto"]} !important;
    border: 1px solid {c["borde"]} !important; border-radius: 14px !important;
    box-shadow: 0 4px 14px {c["sombra"]}; transition: box-shadow 0.25s, border-color 0.25s; }}
.stApp textarea:focus {{ border-color: {c["principal"]} !important; box-shadow: 0 0 0 4px {c["brillo"]}; }}
.stApp [data-testid="stTextArea"] > div > div {{ border: none !important; background: transparent !important; }}
.stApp [data-testid="stCaptionContainer"] p {{ color: {c["suave"]}; }}

/* botón Analizar: sube un poco al pasar el mouse */
.stApp button[kind="primary"] {{ background: {c["principal"]}; border: none; border-radius: 12px;
    padding: 0.55rem 1.8rem; box-shadow: 0 6px 16px {c["brillo"]}; transition: transform 0.2s, box-shadow 0.2s; }}
.stApp button[kind="primary"]:hover {{ transform: translateY(-2px); box-shadow: 0 10px 22px {c["brillo"]}; }}
.stApp button[kind="primary"]:active {{ transform: scale(0.97); }}
.stApp button[kind="primary"] p {{ color: {c["texto_boton"]}; font-weight: 600; }}

/* botón día / noche fijo en la esquina: el icono gira al pasar el mouse */
.st-key-boton_modo {{ position: fixed; top: 4rem; right: 1.5rem; z-index: 999999; width: auto; }}
.st-key-boton_modo button {{ background: {c["tarjeta"]}; color: {c["texto"]};
    border: 1px solid {c["borde"]}; border-radius: 999px; box-shadow: 0 4px 12px {c["sombra"]};
    transition: transform 0.2s; }}
.st-key-boton_modo button:hover {{ transform: scale(1.06); border-color: {c["principal"]}; }}
.st-key-boton_modo button span {{ transition: transform 0.5s; }}
.st-key-boton_modo button:hover span {{ transform: rotate(180deg); }}

/* banner del título con degradado en movimiento */
@keyframes mover {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }} }}
.banner {{ background: {c["banner"]}; background-size: 200% 200%; animation: mover 10s ease infinite;
    border-radius: 20px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
    box-shadow: 0 14px 34px {c["brillo"]}; }}
.banner h1 {{ color: #FFFFFF !important; font-size: 2.1rem; margin: 0; padding: 0; }}
.banner p {{ color: #E0E7FF !important; margin: 0.4rem 0 0 0; }}

/* tarjeta del resultado: aparece deslizándose y la barra se llena */
@keyframes aparecer {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes llenar {{ from {{ width: 0; }} }}
.resultado {{ border-radius: 16px; padding: 1.1rem 1.4rem; margin-top: 1rem; border-left: 6px solid;
    box-shadow: 0 8px 24px {c["sombra"]}; animation: aparecer 0.5s ease-out; }}
.resultado .clase {{ font-size: 1.6rem; font-weight: 700; letter-spacing: 1px; }}
.resultado .detalle {{ color: {c["suave"]} !important; margin: 0.2rem 0 0.8rem 0; }}
.barra {{ position: relative; height: 12px; border-radius: 999px; background: {c["borde"]}; }}
.relleno {{ height: 100%; border-radius: 999px; animation: llenar 1.2s ease-out; }}
.umbral {{ position: absolute; left: 50%; top: -4px; width: 2px; height: 20px; background: {c["suave"]}; }}
.marcas {{ display: flex; justify-content: space-between; font-size: 0.75rem; color: {c["suave"]}; margin-top: 0.3rem; }}

/* tarjetas de métricas: suben y muestran qué significa cada una al pasar el mouse */
.metricas {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; align-items: start; }}
.metrica {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px;
    padding: 0.7rem 0.85rem; box-shadow: 0 3px 10px {c["sombra"]}; cursor: default;
    transition: transform 0.25s, box-shadow 0.25s, border-color 0.25s; }}
.metrica:hover {{ transform: translateY(-4px) scale(1.03); border-color: {c["principal"]};
    box-shadow: 0 12px 24px {c["brillo"]}; }}
.metrica .valor {{ font-size: 1.2rem; font-weight: 700; color: {c["principal"]}; }}
.metrica .nombre {{ font-size: 0.75rem; color: {c["suave"]}; font-weight: 600; }}
.metrica .info {{ font-size: 0.7rem; color: {c["suave"]}; max-height: 0; opacity: 0; overflow: hidden;
    transition: max-height 0.35s, opacity 0.35s, margin 0.35s; }}
.metrica:hover .info {{ max-height: 6rem; opacity: 1; margin-top: 0.35rem; }}
/* botones de ejemplo y botón Limpiar */
.stApp button[kind="secondary"] {{ background: {c["tarjeta"]}; color: {c["texto"]}; border: 1px solid {c["borde"]};
    border-radius: 999px; transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s; }}
.stApp button[kind="secondary"]:hover {{ transform: translateY(-2px); border-color: {c["principal"]};
    color: {c["principal"]}; box-shadow: 0 6px 14px {c["brillo"]}; }}
.stApp button[kind="secondary"] p {{ font-size: 0.85rem; }}
.subtitulo {{ font-weight: 600; margin: 1.2rem 0 0.5rem 0 !important; }}
.contador {{ font-size: 0.8rem; color: {c["suave"]} !important; text-align: right; margin-top: -0.6rem !important; }}
.nota {{ font-size: 0.78rem; color: {c["suave"]} !important; margin-top: 0.5rem !important; }}

/* tarjetas de características del correo */
.caracts {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; animation: aparecer 0.6s ease-out; }}
.caract {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px; padding: 0.7rem 0.9rem;
    box-shadow: 0 3px 10px {c["sombra"]}; transition: transform 0.25s, border-color 0.25s; }}
.caract:hover {{ transform: translateY(-3px); border-color: {c["principal"]}; }}
.caract .valor {{ font-size: 1.3rem; font-weight: 700; color: {c["principal"]}; }}
.caract .nombre {{ font-size: 0.8rem; font-weight: 600; }}
.caract .prom {{ font-size: 0.68rem; color: {c["suave"]}; margin-top: 0.2rem; }}

/* texto con palabras resaltadas */
.texto-marcado {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px;
    padding: 0.9rem 1.1rem; line-height: 1.8; box-shadow: 0 3px 10px {c["sombra"]}; animation: aparecer 0.7s ease-out; }}
mark.urgencia {{ background: rgba(245,158,11,0.30); color: inherit; border-radius: 4px; padding: 0 3px; }}
mark.enlace {{ background: rgba(139,92,246,0.25); color: inherit; border-radius: 4px; padding: 0 3px; }}
[data-testid="stExpander"] details {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px; }}
table.historial {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 0.8rem; }}
table.historial th {{ text-align: left; color: {c["suave"]}; font-weight: 600; border-bottom: 1px solid {c["borde"]}; padding: 0.4rem; }}
table.historial td {{ color: {c["texto"]}; border-bottom: 1px solid {c["borde"]}; padding: 0.4rem; }}
table.historial tr:hover td {{ background: {c["brillo"]}; }}
@media (max-width: 640px) {{ .caracts {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
""", unsafe_allow_html=True)

# botón de la esquina: muestra el modo al que se va a cambiar
with st.container(key="boton_modo"):
    if st.session_state.oscuro:
        st.button("Día", icon=":material/light_mode:", on_click=cambiar_modo)
    else:
        st.button("Noche", icon=":material/dark_mode:", on_click=cambiar_modo)

# panel lateral con la información del modelo
metricas = [("Accuracy", "0.9766", "Correos bien clasificados en total."),
            ("Precision", "0.9633", "De los marcados como phishing, cuántos sí lo eran."),
            ("Recall", "0.9746", "De los phishing reales, cuántos detectó."),
            ("F1-score", "0.9689", "Equilibrio entre precision y recall."),
            ("Falsos positivos", "0.0222", "Correos legítimos marcados como phishing."),
            ("AUC", "0.997", "Qué tan bien separa las dos clases (1 es perfecto).")]
with st.sidebar:
    st.header("Sobre el modelo")
    st.write("**Data-set:** Phishing Email Detection (Kaggle), 17 536 correos después de la limpieza.")
    st.write("**Modelo:** regresión logística con TF-IDF (5000 términos) y 6 características del texto.")
    st.write("**Resultados en la prueba (5 261 correos):**")
    st.caption("Pasa el mouse por una tarjeta para ver qué significa.")
    tarjetas = "".join(f'<div class="metrica"><div class="valor">{v}</div><div class="nombre">{n}</div>'
                       f'<div class="info">{d}</div></div>' for n, v, d in metricas)
    st.markdown(f'<div class="metricas">{tarjetas}</div>', unsafe_allow_html=True)

st.markdown("""
<div class="banner">
  <h1>Detector de correos de phishing</h1>
  <p>Pega el texto de un correo en inglés y el sistema dirá si es phishing o legítimo.</p>
</div>
""", unsafe_allow_html=True)

# correos de ejemplo (los mismos 6 del punto 6.2 del Colab)
EJEMPLOS = {
    "Reporte (legítimo)": "Hi John, attached is the report for tomorrow's meeting. Let me know if you have any questions. Thanks, Maria",
    "Almuerzo (legítimo)": "Reminder: the team lunch was moved to Friday at 1 pm. See you there.",
    "Profesor (legítimo)": "Hello professor, I am sending you the homework for chapter 4. Best regards, Franco",
    "Cuenta (phishing)": "URGENT: Your account has been suspended! Verify your password immediately at http://paypa1-secure.com/login",
    "Premio (phishing)": "Congratulations!!! You have won $1,000,000. Click here to claim your prize now: http://free-prize.win",
    "Banco (phishing)": "Dear customer, we detected unusual activity in your bank account. Please login and confirm your details within 24 hours.",
}

# promedios de cada característica por clase (tabla del punto 3.2 del Colab)
CARACTERISTICAS = [  # (columna, nombre, promedio phishing, promedio legítimo)
    ("n_urls", "Enlaces", 0.292, 0.771),
    ("n_caracteres", "Caracteres", 1641.607, 1848.656),
    ("n_palabras", "Palabras", 311.555, 350.052),
    ("prop_mayus", "Mayúsculas", 0.027, 0.022),
    ("n_exclam", 'Signos "!"', 3.385, 0.638),
    ("n_urgencia", "Palabras de urgencia", 1.081, 0.352),
]

if "historial" not in st.session_state:
    st.session_state.historial = []

def poner_ejemplo(correo):
    st.session_state.texto = correo

def limpiar():
    st.session_state.texto = ""

def formato(col, valor):
    if col == "prop_mayus":
        return f"{valor * 100:.1f} %"
    if col in ("n_caracteres", "n_palabras"):
        return f"{valor:.0f}"
    return f"{valor:g}"

def resaltar(t):
    # marca los enlaces y las palabras de urgencia dentro del correo
    t = html.escape(t)
    def cambiar(m):
        tipo = "enlace" if m.group(1) else "urgencia"
        return f'<mark class="{tipo}">{m.group(0)}</mark>'
    t = patron_resaltar.sub(cambiar, t)
    return t.replace("$", "&#36;").replace("\n", "<br>")

patron_resaltar = re.compile(r"(http\S+|www\.\S+)|\b(" + "|".join(URGENCIA) + r")\b", re.I)

# 1. botones con correos de ejemplo
st.markdown('<p class="subtitulo">Prueba con un correo de ejemplo:</p>', unsafe_allow_html=True)
with st.container(key="ejemplos"):
    columnas = st.columns(3)
    for k, (nombre, correo) in enumerate(EJEMPLOS.items()):
        columnas[k % 3].button(nombre, on_click=poner_ejemplo, args=(correo,), width="stretch")

texto = st.text_area("Texto del correo", height=200, key="texto",
                     placeholder="Pega aquí el texto del correo en inglés...")

# 4. contador de palabras y caracteres
st.markdown(f'<p class="contador">{len(texto.split())} palabras &middot; {len(texto)} caracteres</p>',
            unsafe_allow_html=True)

col1, col2, _ = st.columns([1.2, 1, 3])
analizar = col1.button("Analizar", type="primary", width="stretch")
col2.button("Limpiar", on_click=limpiar, width="stretch")

if analizar:
    if texto.strip() == "":
        st.warning("Primero pega el texto de un correo.")
    else:
        fila = pd.DataFrame([{"texto_limpio": limpiar_texto(texto), **estructurales(texto)}])
        p = modelo.predict_proba(fila)[0, 1]          # probabilidad de phishing
        st.session_state.ultimo = {"texto": texto, "p": p}
        # 5. historial de la sesión
        nuevo = {"Correo": texto[:50] + ("..." if len(texto) > 50 else ""),
                 "Resultado": "PHISHING" if p >= 0.5 else "LEGÍTIMO",
                 "P(phishing)": f"{p * 100:.1f} %"}
        if not st.session_state.historial or st.session_state.historial[0] != nuevo:   # sin repetidos seguidos
            st.session_state.historial.insert(0, nuevo)

# el resultado se muestra mientras el texto no cambie
ultimo = st.session_state.get("ultimo")
if ultimo and ultimo["texto"] == texto and texto.strip() != "":
    p = ultimo["p"]
    if p >= 0.5:
        clase, color, fondo = "PHISHING", c["rojo"], c["rojo_fondo"]
        detalle = f"PHISHING - probabilidad: {p * 100:.1f} %"
    else:
        clase, color, fondo = "LEGÍTIMO", c["verde"], c["verde_fondo"]
        detalle = f"LEGÍTIMO - probabilidad de phishing: {p * 100:.1f} %"
    st.markdown(f"""
<div class="resultado" style="background:{fondo}; border-color:{color};">
<div class="clase" style="color:{color};">{clase}</div>
<p class="detalle">{detalle}</p>
<div class="barra"><div class="relleno" style="width:{p * 100:.1f}%; background:{color};"></div><div class="umbral"></div></div>
<div class="marcas"><span>0 %</span><span>umbral 50 %</span><span>100 %</span></div>
</div>
""", unsafe_allow_html=True)

    # 2. características del correo comparadas con los promedios del data-set
    valores = estructurales(texto)
    cajas = ""
    for col, nombre, prom_ph, prom_leg in CARACTERISTICAS:
        cajas += (f'<div class="caract"><div class="valor">{formato(col, valores[col])}</div>'
                  f'<div class="nombre">{nombre}</div>'
                  f'<div class="prom">Promedio: phishing {formato(col, prom_ph)} | legítimo {formato(col, prom_leg)}</div></div>')
    st.markdown(f"""
<p class="subtitulo">Características del correo</p>
<div class="caracts">{cajas}</div>
<p class="nota">El modelo usa estas 6 medidas junto con las palabras del texto (TF-IDF). Debajo de cada una está el promedio de los correos del data-set.</p>
""", unsafe_allow_html=True)

    # 3. texto con los enlaces y las palabras de urgencia resaltados
    st.markdown(f"""
<p class="subtitulo">Texto analizado</p>
<div class="texto-marcado">{resaltar(texto)}</div>
<p class="nota"><mark class="urgencia">palabra de urgencia</mark> &nbsp; <mark class="enlace">enlace</mark></p>
""", unsafe_allow_html=True)

# 5. historial de los correos analizados
if st.session_state.historial:
    with st.expander(f"Historial de esta sesión ({len(st.session_state.historial)})"):
        filas = "".join(
            f'<tr><td>{html.escape(h["Correo"])}</td>'
            f'<td style="color:{c["rojo"] if h["Resultado"] == "PHISHING" else c["verde"]}; font-weight:600;">{h["Resultado"]}</td>'
            f'<td>{h["P(phishing)"]}</td></tr>' for h in st.session_state.historial)
        st.markdown(f'<table class="historial"><tr><th>Correo</th><th>Resultado</th><th>P(phishing)</th></tr>{filas}</table>',
                    unsafe_allow_html=True)
        if st.button("Borrar historial"):
            st.session_state.historial = []
            st.rerun()

st.write("")
st.caption("Aprendizaje Estadístico - UPAO 2026-II | Eustaquio Ávila, Marquez Rodriguez, Velásquez Revilla")
