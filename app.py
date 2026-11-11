import joblib
import pandas as pd
import streamlit as st
from procesamiento import limpiar_texto, estructurales

@st.cache_resource
def cargar_modelo():
    return joblib.load("modelo_phishing.joblib")

modelo = cargar_modelo()

st.title("Detector de correos de phishing")
st.write("Pega el texto de un correo en inglés y el sistema dirá si es phishing o legítimo.")

texto = st.text_area("Texto del correo", height=220)

if st.button("Analizar"):
    if texto.strip() == "":
        st.warning("Primero pega el texto de un correo.")
    else:
        fila = pd.DataFrame([{"texto_limpio": limpiar_texto(texto), **estructurales(texto)}])
        p = modelo.predict_proba(fila)[0, 1]
        if p >= 0.5:
            st.error(f"PHISHING - probabilidad: {p * 100:.1f} %")
        else:
            st.success(f"LEGÍTIMO - probabilidad de phishing: {p * 100:.1f} %")

st.caption("Aprendizaje Estadístico - UPAO 2026-II | Eustaquio Ávila, Marquez Rodriguez, Velásquez Revilla")
