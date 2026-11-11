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
    c = {"fondo": "#0B1120", "fondo2": "#111A2E", "tarjeta": "#16213A", "borde": "#26324D",
         "texto": "#E2E8F0", "suave": "#94A3B8", "principal": "#60A5FA", "texto_boton": "#0B1120",
         "banner": "linear-gradient(135deg, #1E3A8A 0%, #5B21B6 100%)",
         "rojo": "#F87171", "rojo_fondo": "rgba(248,113,113,0.12)",
         "verde": "#4ADE80", "verde_fondo": "rgba(74,222,128,0.12)"}
else:
    c = {"fondo": "#F4F7FB", "fondo2": "#FFFFFF", "tarjeta": "#FFFFFF", "borde": "#DCE3EE",
         "texto": "#0F172A", "suave": "#64748B", "principal": "#1D4ED8", "texto_boton": "#FFFFFF",
         "banner": "linear-gradient(135deg, #1D4ED8 0%, #7C3AED 100%)",
         "rojo": "#B91C1C", "rojo_fondo": "#FEECEC",
         "verde": "#15803D", "verde_fondo": "#E9F8EF"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
.stApp {{ background: {c["fondo"]}; }}
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3 {{
    color: {c["texto"]}; font-family: 'Poppins', sans-serif; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: {c["fondo2"]}; border-right: 1px solid {c["borde"]}; }}
.stApp textarea {{ background: {c["tarjeta"]} !important; color: {c["texto"]} !important;
    border: 1px solid {c["borde"]} !important; border-radius: 12px !important; }}
.stApp [data-testid="stTextArea"] > div > div {{ border: none !important; background: transparent !important; }}
.stApp [data-testid="stCaptionContainer"] p {{ color: {c["suave"]}; }}
.stApp button[kind="primary"] {{ background: {c["principal"]}; border: none; border-radius: 10px;
    padding: 0.5rem 1.6rem; }}
.stApp button[kind="primary"] p {{ color: {c["texto_boton"]}; font-weight: 600; }}

/* botón día / noche fijo en la esquina */
.st-key-boton_modo {{ position: fixed; top: 4rem; right: 1.5rem; z-index: 999999; width: auto; }}
.st-key-boton_modo button {{ background: {c["tarjeta"]}; color: {c["texto"]};
    border: 1px solid {c["borde"]}; border-radius: 999px; }}

/* banner del título */
.banner {{ background: {c["banner"]}; border-radius: 18px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
    box-shadow: 0 10px 30px rgba(29,78,216,0.25); }}
.banner h1 {{ color: #FFFFFF !important; font-size: 2.1rem; margin: 0; padding: 0; }}
.banner p {{ color: #E0E7FF !important; margin: 0.4rem 0 0 0; }}

/* tarjeta del resultado */
.resultado {{ border-radius: 14px; padding: 1.1rem 1.4rem; margin-top: 1rem; border-left: 6px solid; }}
.resultado .clase {{ font-size: 1.6rem; font-weight: 700; letter-spacing: 1px; }}
.resultado .detalle {{ color: {c["suave"]} !important; margin: 0.2rem 0 0.8rem 0; }}
.barra {{ position: relative; height: 12px; border-radius: 999px; background: {c["borde"]}; }}
.relleno {{ height: 100%; border-radius: 999px; }}
.umbral {{ position: absolute; left: 50%; top: -4px; width: 2px; height: 20px; background: {c["suave"]}; }}
.marcas {{ display: flex; justify-content: space-between; font-size: 0.75rem; color: {c["suave"]}; margin-top: 0.3rem; }}

/* tarjetas de métricas del panel lateral */
.metricas {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }}
.metrica {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 12px; padding: 0.6rem 0.8rem; }}
.metrica .valor {{ font-size: 1.15rem; font-weight: 700; color: {c["principal"]}; }}
.metrica .nombre {{ font-size: 0.75rem; color: {c["suave"]}; }}
</style>
""", unsafe_allow_html=True)

# botón de la esquina: muestra el modo al que se va a cambiar
with st.container(key="boton_modo"):
    if st.session_state.oscuro:
        st.button("Día", icon=":material/light_mode:", on_click=cambiar_modo)
    else:
        st.button("Noche", icon=":material/dark_mode:", on_click=cambiar_modo)

# panel lateral con la información del modelo
metricas = [("Accuracy", "0.9766"), ("Precision", "0.9633"), ("Recall", "0.9746"),
            ("F1-score", "0.9689"), ("Falsos positivos", "0.0222"), ("AUC", "0.997")]
with st.sidebar:
    st.header("Sobre el modelo")
    st.write("**Data-set:** Phishing Email Detection (Kaggle), 17 536 correos después de la limpieza.")
    st.write("**Modelo:** regresión logística con TF-IDF (5000 términos) y 6 características del texto.")
    st.write("**Resultados en la prueba (5 261 correos):**")
    tarjetas = "".join(f'<div class="metrica"><div class="valor">{v}</div><div class="nombre">{n}</div></div>'
                       for n, v in metricas)
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
