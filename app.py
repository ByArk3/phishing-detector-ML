import joblib
import pandas as pd
import streamlit as st
from procesamiento import limpiar_texto, estructurales

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

texto = st.text_area("Texto del correo", height=220)

if st.button("Analizar", type="primary"):
    if texto.strip() == "":
        st.warning("Primero pega el texto de un correo.")
    else:
        fila = pd.DataFrame([{"texto_limpio": limpiar_texto(texto), **estructurales(texto)}])
        p = modelo.predict_proba(fila)[0, 1]          # probabilidad de phishing
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

st.write("")
st.caption("Aprendizaje Estadístico - UPAO 2026-II | Eustaquio Ávila, Marquez Rodriguez, Velásquez Revilla")
