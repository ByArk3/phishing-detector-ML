import joblib
import pandas as pd
import streamlit as st
from procesamiento import limpiar_texto, estructurales

st.set_page_config(page_title="Detector de phishing", layout="centered")

@st.cache_resource
def cargar_modelo():
    return joblib.load("modelo_phishing.joblib")

modelo = cargar_modelo()

# panel lateral con la información del modelo
with st.sidebar:
    st.header("Sobre el modelo")
    st.write("**Data-set:** Phishing Email Detection (Kaggle), 17 536 correos después de la limpieza.")
    st.write("**Modelo:** regresión logística con TF-IDF (5000 términos) y 6 características del texto.")
    st.write("**Resultados en la prueba (5 261 correos):**")
    st.table(pd.DataFrame({
        "Métrica": ["Accuracy", "Precision", "Recall", "F1-score", "Tasa de falsos positivos", "AUC"],
        "Resultado": ["0.9766", "0.9633", "0.9746", "0.9689", "0.0222", "0.997"],
    }).set_index("Métrica"))

st.title("Detector de correos de phishing")
st.write("Pega el texto de un correo en inglés y el sistema dirá si es phishing o legítimo.")

texto = st.text_area("Texto del correo", height=220)

if st.button("Analizar", type="primary"):
    if texto.strip() == "":
        st.warning("Primero pega el texto de un correo.")
    else:
        fila = pd.DataFrame([{"texto_limpio": limpiar_texto(texto), **estructurales(texto)}])
        p = modelo.predict_proba(fila)[0, 1]
        if p >= 0.5:
            st.error(f"PHISHING - probabilidad: {p * 100:.1f} %")
        else:
            st.success(f"LEGÍTIMO - probabilidad de phishing: {p * 100:.1f} %")
        # barra con la probabilidad de phishing
        st.progress(float(p), text=f"Probabilidad de phishing: {p * 100:.1f} % (umbral: 50 %)")

st.caption("Aprendizaje Estadístico - UPAO 2026-II | Eustaquio Ávila, Marquez Rodriguez, Velásquez Revilla")
