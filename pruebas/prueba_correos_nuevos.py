# Prueba del modelo guardado con los 6 correos nuevos del punto 6.2 del Colab.
# Se ejecuta desde la carpeta principal: python pruebas/prueba_correos_nuevos.py
import sys
from pathlib import Path

import joblib
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from procesamiento import limpiar_texto, estructurales

modelo = joblib.load(RAIZ / "modelo_phishing.joblib")

# mismos correos del Colab (celda "Prueba del sistema con correos nuevos")
nuevos = [
    ("Hi John, attached is the report for tomorrow's meeting. Let me know if you have any questions. Thanks, Maria", "LEGÍTIMO"),
    ("Reminder: the team lunch was moved to Friday at 1 pm. See you there.", "LEGÍTIMO"),
    ("Hello professor, I am sending you the homework for chapter 4. Best regards, Franco", "LEGÍTIMO"),
    ("URGENT: Your account has been suspended! Verify your password immediately at http://paypa1-secure.com/login", "PHISHING"),
    ("Congratulations!!! You have won $1,000,000. Click here to claim your prize now: http://free-prize.win", "PHISHING"),
    ("Dear customer, we detected unusual activity in your bank account. Please login and confirm your details within 24 hours.", "PHISHING"),
]

filas = []
for texto, esperado in nuevos:
    fila = pd.DataFrame([{"texto_limpio": limpiar_texto(texto), **estructurales(texto)}])
    p = modelo.predict_proba(fila)[0, 1]          # probabilidad de phishing
    predicho = "PHISHING" if p >= 0.5 else "LEGÍTIMO"
    filas.append({"Correo": texto[:45] + "...", "Esperado": esperado, "Predicho": predicho,
                  "P(phishing)": f"{p:.4f}", "¿Acierta?": "Sí" if predicho == esperado else "No"})

tabla = pd.DataFrame(filas)
print(tabla.to_string(index=False))
print("\nAciertos:", (tabla["¿Acierta?"] == "Sí").sum(), "de", len(tabla))
