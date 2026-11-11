import html
import re
import joblib
import pandas as pd
import streamlit as st
from procesamiento import limpiar_texto, estructurales, URGENCIA, patron_url, patron_urg

st.set_page_config(page_title="Detector de phishing", layout="centered")

# ---------- datos fijos ----------

# colores de la app (modo noche)
c = {"fondo": "radial-gradient(circle at 15% 0%, #1E1B4B 0%, #0B1120 45%)",
     "tarjeta": "#16213A", "borde": "#26324D", "sombra": "rgba(0,0,0,0.45)",
     "texto": "#E2E8F0", "suave": "#94A3B8", "principal": "#60A5FA", "texto_boton": "#0B1120",
     "brillo": "rgba(96,165,250,0.35)",
     "banner": "linear-gradient(120deg, #1E3A8A, #5B21B6, #1E3A8A)",
     "rojo": "#F87171", "rojo_fondo": "rgba(248,113,113,0.12)",
     "verde": "#4ADE80", "verde_fondo": "rgba(74,222,128,0.12)"}

# métricas oficiales del Colab (conjunto de prueba)
METRICAS = [("Accuracy", "0.9766", "Correos bien clasificados en total."),
            ("Precision", "0.9633", "De los marcados como phishing, cuántos sí lo eran."),
            ("Recall", "0.9746", "De los phishing reales, cuántos detectó."),
            ("F1-score", "0.9689", "Equilibrio entre precision y recall."),
            ("Falsos positivos", "0.0222", "Correos legítimos marcados como phishing."),
            ("AUC", "0.997", "Qué tan bien separa las dos clases (1 es perfecto).")]

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

# enlaces (grupo 1) o palabras de urgencia (grupo 2), para resaltarlos en el texto
patron_resaltar = re.compile(r"(http\S+|www\.\S+)|\b(" + "|".join(URGENCIA) + r")\b", re.I)

# ---------- modelo ----------

@st.cache_resource
def cargar_modelo():
    return joblib.load("modelo_phishing.joblib")

modelo = cargar_modelo()

@st.cache_data
def palabras_importantes():
    # palabras con más peso en la regresión logística (coeficientes del TF-IDF)
    vocab = modelo.named_steps["preprocesador"].named_transformers_["tfidf"].get_feature_names_out()
    coef = modelo.named_steps["modelo"].coef_[0][:len(vocab)]
    orden = coef.argsort()
    phishing = [(vocab[i], float(coef[i])) for i in orden[::-1][:10]]
    legitimo = [(vocab[i], float(coef[i])) for i in orden[:10]]
    return phishing, legitimo

# ---------- funciones de apoyo ----------

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
    def cambiar(m):
        tipo = "enlace" if m.group(1) else "urgencia"
        return f'<mark class="{tipo}">{m.group(0)}</mark>'
    t = patron_resaltar.sub(cambiar, html.escape(t))
    return t.replace("$", "&#36;").replace("\n", "<br>")

def encontrados(t, patron):
    # lo que encontró el modelo (con la misma regla), sin repetir y con cuántas veces aparece
    conteo = {}
    for x in patron.findall(t):
        conteo.setdefault(x.lower(), [x, 0])[1] += 1
    lista = [f"{x} (x{n})" if n > 1 else x for x, n in conteo.values()]
    return html.escape(", ".join(lista)) if lista else "Ninguno"

def barras(lista, color, maximo):
    filas = ""
    for palabra, valor in lista:
        filas += (f'<div class="fila-p" title="Coeficiente: {valor:+.2f}"><span class="pal">{palabra}</span>'
                  f'<div class="pista"><div class="llena" style="width:{abs(valor) / maximo * 100:.0f}%; background:{color};"></div></div>'
                  f'<span class="num">{valor:+.2f}</span></div>')
    return filas

# ---------- estilos ----------

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
.stApp {{ background: {c["fondo"]}; }}
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3 {{
    color: {c["texto"]}; font-family: 'Poppins', sans-serif; }}
[data-testid="stHeader"] {{ background: transparent; }}
.stApp [data-testid="stCaptionContainer"] p {{ color: {c["suave"]}; }}
.subtitulo {{ font-weight: 600; margin: 1.2rem 0 0.5rem 0 !important; }}
.nota {{ font-size: 0.78rem; color: {c["suave"]} !important; margin-top: 0.5rem !important; }}

/* animaciones */
@keyframes mover {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }} }}
@keyframes aparecer {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes llenar {{ from {{ width: 0; }} }}
@keyframes flotar {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}

/* banner del título: degradado en movimiento e ícono */
.banner {{ display: flex; align-items: center; justify-content: space-between; gap: 1.5rem;
    background: {c["banner"]}; background-size: 200% 200%; animation: mover 10s ease infinite;
    border-radius: 20px; padding: 1.8rem 2rem; margin-bottom: 1.5rem; box-shadow: 0 14px 34px {c["brillo"]}; }}
.banner h1 {{ color: #FFFFFF !important; font-size: 2.1rem; margin: 0; padding: 0; }}
.banner p {{ color: #E0E7FF !important; margin: 0.4rem 0 0 0; }}
.banner .etiqueta {{ display: inline-block; font-size: 0.72rem; font-weight: 600; letter-spacing: 1px; color: #E0E7FF;
    background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.25); border-radius: 999px;
    padding: 0.15rem 0.7rem; margin-bottom: 0.6rem; }}
.banner .escudo {{ flex-shrink: 0; width: 92px; height: 92px; animation: flotar 4s ease-in-out infinite;
    filter: drop-shadow(0 8px 18px rgba(0,0,0,0.35)); }}

/* tarjetas que muestran una explicación al pasar el mouse (cifras de arriba y métricas) */
.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.7rem; align-items: start; margin: -0.4rem 0 1.4rem 0; }}
.metricas {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; align-items: start; }}
.kpi, .metrica {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 16px;
    box-shadow: 0 4px 14px {c["sombra"]}; cursor: default; transition: transform 0.25s, border-color 0.25s, box-shadow 0.25s; }}
.kpi:hover, .metrica:hover {{ transform: translateY(-4px); border-color: {c["principal"]}; box-shadow: 0 12px 26px {c["brillo"]}; }}
.kpi .info, .metrica .info {{ font-size: 0.72rem; max-height: 0; opacity: 0; overflow: hidden;
    transition: max-height 0.35s, opacity 0.35s, margin 0.35s; }}
.kpi:hover .info, .metrica:hover .info {{ max-height: 5rem; opacity: 1; margin-top: 0.4rem; }}
.kpi {{ padding: 0.9rem 1rem; text-align: center; animation: aparecer 0.6s ease-out both; }}
.kpi:nth-child(2) {{ animation-delay: 0.1s; }} .kpi:nth-child(3) {{ animation-delay: 0.2s; }} .kpi:nth-child(4) {{ animation-delay: 0.3s; }}
.kpi .grande {{ font-size: 1.7rem; font-weight: 700; background: linear-gradient(90deg, #60A5FA, #A78BFA);
    -webkit-background-clip: text; background-clip: text; color: transparent; }}
.kpi .chico {{ font-size: 0.75rem; color: {c["suave"]}; }}
.kpi .info {{ color: {c["texto"]}; }}
.metrica {{ padding: 0.7rem 0.85rem; }}
.metrica .valor {{ font-size: 1.2rem; font-weight: 700; color: {c["principal"]}; }}
.metrica .nombre {{ font-size: 0.75rem; color: {c["suave"]}; font-weight: 600; }}
.metrica .info {{ color: {c["suave"]}; }}

/* pestañas */
.stTabs [data-baseweb="tab-list"] {{ gap: 0.4rem; }}
.stTabs [data-baseweb="tab"] {{ background: {c["tarjeta"]}; border-radius: 10px 10px 0 0; padding: 0.4rem 1rem; }}
.stTabs [data-baseweb="tab"] p {{ font-weight: 600; }}

/* cuadro de texto: se ilumina al escribir */
.stApp textarea {{ background: {c["tarjeta"]} !important; color: {c["texto"]} !important;
    border: 1px solid {c["borde"]} !important; border-radius: 14px !important;
    box-shadow: 0 4px 14px {c["sombra"]}; transition: box-shadow 0.25s, border-color 0.25s; }}
.stApp textarea:focus {{ border-color: {c["principal"]} !important; box-shadow: 0 0 0 4px {c["brillo"]}; }}
.stApp [data-testid="stTextArea"] > div > div {{ border: none !important; background: transparent !important; }}
.contador {{ font-size: 0.8rem; color: {c["suave"]} !important; text-align: right; margin-top: -0.6rem !important; }}

/* botones: Analizar (principal) y ejemplos / Limpiar (secundarios) */
.stApp button[kind="primary"] {{ background: {c["principal"]}; border: none; border-radius: 12px;
    padding: 0.55rem 1.8rem; box-shadow: 0 6px 16px {c["brillo"]}; transition: transform 0.2s, box-shadow 0.2s; }}
.stApp button[kind="primary"]:hover {{ transform: translateY(-2px); box-shadow: 0 10px 22px {c["brillo"]}; }}
.stApp button[kind="primary"]:active {{ transform: scale(0.97); }}
.stApp button[kind="primary"] p {{ color: {c["texto_boton"]}; font-weight: 600; }}
.stApp button[kind="secondary"] {{ background: {c["tarjeta"]}; color: {c["texto"]}; border: 1px solid {c["borde"]};
    border-radius: 999px; transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s; }}
.stApp button[kind="secondary"]:hover {{ transform: translateY(-2px); border-color: {c["principal"]};
    color: {c["principal"]}; box-shadow: 0 6px 14px {c["brillo"]}; }}
.stApp button[kind="secondary"] p {{ font-size: 0.85rem; }}

/* resultado: aparece deslizándose y la barra se llena */
.resultado {{ border-radius: 16px; padding: 1.1rem 1.4rem; margin-top: 1rem; border-left: 6px solid;
    box-shadow: 0 8px 24px {c["sombra"]}; animation: aparecer 0.5s ease-out; }}
.resultado .clase {{ font-size: 1.6rem; font-weight: 700; letter-spacing: 1px; }}
.resultado .detalle {{ color: {c["suave"]} !important; margin: 0.2rem 0 0.8rem 0; }}
.barra {{ position: relative; height: 12px; border-radius: 999px; background: {c["borde"]}; }}
.relleno {{ height: 100%; border-radius: 999px; animation: llenar 1.2s ease-out; }}
.umbral {{ position: absolute; left: 50%; top: -4px; width: 2px; height: 20px; background: {c["suave"]}; }}
.marcas {{ display: flex; justify-content: space-between; font-size: 0.75rem; color: {c["suave"]}; margin-top: 0.3rem; }}

/* características del correo */
.caracts {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; animation: aparecer 0.6s ease-out; }}
.caract {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px; padding: 0.7rem 0.9rem;
    box-shadow: 0 3px 10px {c["sombra"]}; transition: transform 0.25s, border-color 0.25s; }}
.caract:hover {{ transform: translateY(-3px); border-color: {c["principal"]}; }}
.caract .valor {{ font-size: 1.3rem; font-weight: 700; color: {c["principal"]}; }}
.caract .nombre {{ font-size: 0.8rem; font-weight: 600; }}
.caract .prom {{ font-size: 0.68rem; color: {c["suave"]}; margin-top: 0.2rem; }}

/* texto analizado y tabla de lo encontrado */
.texto-marcado {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px;
    padding: 0.9rem 1.1rem; line-height: 1.8; box-shadow: 0 3px 10px {c["sombra"]}; animation: aparecer 0.7s ease-out; }}
mark.urgencia {{ background: rgba(245,158,11,0.30); color: inherit; border-radius: 4px; padding: 0 3px; }}
mark.enlace {{ background: rgba(139,92,246,0.25); color: inherit; border-radius: 4px; padding: 0 3px; }}
.leyenda {{ width: 100%; margin-top: 0.8rem; border-collapse: separate; border-spacing: 0; font-size: 0.85rem;
    background: {c["tarjeta"]}; border: 1px solid {c["principal"]}; border-radius: 14px; overflow: hidden;
    box-shadow: 0 0 0 3px {c["brillo"]}, 0 8px 22px {c["sombra"]}; animation: aparecer 0.8s ease-out; }}
.leyenda th {{ text-align: left; padding: 0.55rem 0.8rem; color: {c["texto"]}; font-weight: 600;
    background: linear-gradient(90deg, rgba(30,58,138,0.55), rgba(91,33,182,0.55)); }}
.leyenda td {{ padding: 0.55rem 0.8rem; color: {c["texto"]}; border-top: 1px solid {c["borde"]}; word-break: break-word; }}
.leyenda tr:hover td {{ background: {c["brillo"]}; }}
.leyenda .cantidad {{ font-size: 1.1rem; font-weight: 700; color: {c["principal"]}; text-align: center; }}

/* historial */
[data-testid="stExpander"] details {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px; }}
[data-testid="stExpander"] summary {{ background: {c["tarjeta"]} !important; border-radius: 14px; }}
[data-testid="stExpander"] summary:hover {{ background: {c["borde"]} !important; }}
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span {{ color: {c["texto"]} !important; }}
table.historial {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 0.8rem; }}
table.historial th {{ text-align: left; color: {c["suave"]}; font-weight: 600; border-bottom: 1px solid {c["borde"]}; padding: 0.4rem; }}
table.historial td {{ color: {c["texto"]}; border-bottom: 1px solid {c["borde"]}; padding: 0.4rem; }}
table.historial tr:hover td {{ background: {c["brillo"]}; }}

/* pestaña "Sobre el modelo" */
.info-modelo {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px; padding: 0.8rem 1rem; line-height: 1.7; }}
.palabras {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; animation: aparecer 0.6s ease-out; }}
.col-p {{ background: {c["tarjeta"]}; border: 1px solid {c["borde"]}; border-radius: 14px; padding: 0.9rem 1rem;
    box-shadow: 0 3px 10px {c["sombra"]}; }}
.tit-p {{ font-weight: 700; margin-bottom: 0.6rem; letter-spacing: 0.5px; }}
.fila-p {{ display: grid; grid-template-columns: 6.5rem 1fr 3rem; align-items: center; gap: 0.5rem;
    padding: 0.22rem 0.3rem; border-radius: 8px; transition: background 0.2s; }}
.fila-p:hover {{ background: {c["brillo"]}; }}
.pal {{ font-size: 0.85rem; color: {c["texto"]}; font-family: monospace; }}
.pista {{ height: 10px; background: {c["borde"]}; border-radius: 999px; overflow: hidden; }}
.llena {{ height: 100%; border-radius: 999px; animation: llenar 1.2s ease-out; }}
.num {{ font-size: 0.78rem; color: {c["suave"]}; text-align: right; }}
.leyenda-p {{ margin-top: 0.9rem; padding: 0.7rem 0.9rem; font-size: 0.8rem; color: {c["suave"]}; background: {c["tarjeta"]};
    border: 1px solid {c["borde"]}; border-left: 4px solid {c["principal"]}; border-radius: 10px; }}

/* celular */
@media (max-width: 640px) {{
    .kpis, .caracts, .metricas {{ grid-template-columns: repeat(2, 1fr); }}
    .palabras {{ grid-template-columns: 1fr; }}
    .banner .escudo {{ display: none; }}
}}
</style>
""", unsafe_allow_html=True)

# ---------- encabezado: banner y cifras principales ----------

st.markdown("""
<div class="banner">
  <div>
    <span class="etiqueta">APRENDIZAJE ESTADÍSTICO · UPAO 2026-II</span>
    <h1>Detector de correos de phishing</h1>
    <p>Pega el texto de un correo en inglés y el sistema dirá si es phishing o legítimo.</p>
  </div>
  <svg class="escudo" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 2.5 4 5.5v6c0 5 3.4 8.7 8 10 4.6-1.3 8-5 8-10v-6l-8-3Z" fill="rgba(255,255,255,0.12)"/>
    <rect x="7.5" y="9" width="9" height="6.5" rx="1"/><path d="m7.8 9.4 4.2 3.3 4.2-3.3"/>
  </svg>
</div>
<div class="kpis">
  <div class="kpi"><div class="grande">97.7 %</div><div class="chico">de aciertos (accuracy)</div><div class="info">Correos bien clasificados en la prueba (5 261 correos).</div></div>
  <div class="kpi"><div class="grande">0.9689</div><div class="chico">F1-score</div><div class="info">Equilibrio entre precision y recall.</div></div>
  <div class="kpi"><div class="grande">0.997</div><div class="chico">AUC en la prueba</div><div class="info">Qué tan bien separa las dos clases (1 es perfecto).</div></div>
  <div class="kpi"><div class="grande">17 536</div><div class="chico">correos del data-set</div><div class="info">70 % para entrenar y 30 % para probar.</div></div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Analizar", "Sobre el modelo"])

# ---------- pestaña Analizar ----------

with tab1:
    if "historial" not in st.session_state:
        st.session_state.historial = []

    # botones con correos de ejemplo
    st.markdown('<p class="subtitulo">Prueba con un correo de ejemplo:</p>', unsafe_allow_html=True)
    lista = list(EJEMPLOS.items())
    for i in range(0, len(lista), 3):          # filas de 3 botones (en celular quedan en orden)
        for col, (nombre, correo) in zip(st.columns(3), lista[i:i + 3]):
            col.button(nombre, on_click=poner_ejemplo, args=(correo,), width="stretch")

    texto = st.text_area("Texto del correo", height=200, key="texto",
                         placeholder="Pega aquí el texto del correo en inglés...")
    st.markdown(f'<p class="contador">{len(texto.split())} palabras &middot; {len(texto)} caracteres</p>',
                unsafe_allow_html=True)

    col1, col2, _ = st.columns([1.2, 1, 3])
    analizar = col1.button("Analizar", type="primary", width="stretch")
    col2.button("Limpiar", on_click=limpiar, width="stretch")

    if analizar:
        if texto.strip() == "":
            st.warning("Primero pega el texto de un correo.")
        else:
            valores = estructurales(texto)
            fila = pd.DataFrame([{"texto_limpio": limpiar_texto(texto), **valores}])
            p = modelo.predict_proba(fila)[0, 1]          # probabilidad de phishing
            st.session_state.ultimo = {"texto": texto, "p": p, "valores": valores}
            nuevo = {"Correo": texto[:50] + ("..." if len(texto) > 50 else ""),
                     "Resultado": "PHISHING" if p >= 0.5 else "LEGÍTIMO",
                     "P(phishing)": f"{p * 100:.1f} %"}
            if not st.session_state.historial or st.session_state.historial[0] != nuevo:   # sin repetidos seguidos
                st.session_state.historial.insert(0, nuevo)

    # el resultado se muestra mientras el texto no cambie
    ultimo = st.session_state.get("ultimo")
    if ultimo and ultimo["texto"] == texto and texto.strip() != "":
        p, valores = ultimo["p"], ultimo["valores"]
        if p >= 0.5:
            clase, color, fondo = "PHISHING", c["rojo"], c["rojo_fondo"]
            detalle = f"PHISHING - probabilidad: {p * 100:.1f} %"
        else:
            clase, color, fondo = "LEGÍTIMO", c["verde"], c["verde_fondo"]
            detalle = f"LEGÍTIMO - probabilidad de phishing: {p * 100:.1f} %"

        cajas = "".join(
            f'<div class="caract"><div class="valor">{formato(col, valores[col])}</div>'
            f'<div class="nombre">{nombre}</div>'
            f'<div class="prom">Promedio: phishing {formato(col, prom_ph)} | legítimo {formato(col, prom_leg)}</div></div>'
            for col, nombre, prom_ph, prom_leg in CARACTERISTICAS)

        st.markdown(f"""
<div class="resultado" style="background:{fondo}; border-color:{color};">
<div class="clase" style="color:{color};">{clase}</div>
<p class="detalle">{detalle}</p>
<div class="barra"><div class="relleno" style="width:{p * 100:.1f}%; background:{color};"></div><div class="umbral"></div></div>
<div class="marcas"><span>0 %</span><span>umbral 50 %</span><span>100 %</span></div>
</div>
<p class="subtitulo">Características del correo</p>
<div class="caracts">{cajas}</div>
<p class="nota">El modelo usa estas 6 medidas junto con las palabras del texto (TF-IDF). Debajo de cada una está el promedio de los correos del data-set.</p>
<p class="subtitulo">Texto analizado</p>
<div class="texto-marcado">{resaltar(texto)}</div>
<table class="leyenda">
<tr><th>Color</th><th>Qué marca</th><th>Cantidad</th><th>Encontrado en el correo</th></tr>
<tr><td><mark class="urgencia">naranja</mark></td><td>Palabras de urgencia</td><td class="cantidad">{valores["n_urgencia"]}</td><td>{encontrados(texto, patron_urg)}</td></tr>
<tr><td><mark class="enlace">morado</mark></td><td>Enlaces</td><td class="cantidad">{valores["n_urls"]}</td><td>{encontrados(texto, patron_url)}</td></tr>
</table>
""", unsafe_allow_html=True)

    # historial de los correos analizados
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

# ---------- pestaña Sobre el modelo ----------

with tab2:
    tarjetas = "".join(f'<div class="metrica"><div class="valor">{v}</div><div class="nombre">{n}</div>'
                       f'<div class="info">{d}</div></div>' for n, v, d in METRICAS)
    phishing, legitimo = palabras_importantes()
    maximo = max(abs(v) for _, v in phishing + legitimo)
    st.markdown(f"""
<div class="info-modelo"><b>Data-set:</b> Phishing Email Detection (Kaggle), 17 536 correos después de la limpieza.<br>
<b>Modelo:</b> regresión logística con TF-IDF (5000 términos) y 6 características del texto.</div>
<p class="subtitulo">Resultados en la prueba (5 261 correos)</p>
<div class="metricas">{tarjetas}</div>
<p class="subtitulo">Palabras más importantes del modelo</p>
<p class="nota">Son las palabras con el coeficiente más alto en la regresión logística. Un coeficiente positivo empuja hacia phishing y uno negativo hacia legítimo. Pasa el mouse por una barra para ver su valor.</p>
<div class="palabras">
<div class="col-p"><div class="tit-p" style="color:{c["rojo"]};">Más indican PHISHING</div>{barras(phishing, c["rojo"], maximo)}</div>
<div class="col-p"><div class="tit-p" style="color:{c["verde"]};">Más indican LEGÍTIMO</div>{barras(legitimo, c["verde"], maximo)}</div>
</div>
<div class="leyenda-p"><b>Nota:</b> las palabras salen cortadas por el stemming (por ejemplo, "remov" viene de remove y removal). Algunas palabras de legítimo, como "enron", "linguist" o "vinc", aparecen porque muchos correos legítimos del data-set vienen de la empresa Enron y de una lista de lingüística. Es una limitación del data-set: un correo legítimo distinto a esos puede salir como phishing.</div>
""", unsafe_allow_html=True)

st.write("")
st.caption("Aprendizaje Estadístico - UPAO 2026-II | Eustaquio Ávila, Marquez Rodriguez, Velásquez Revilla")
