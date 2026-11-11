# Sistema de detección de correos electrónicos de phishing

Sistema de detección de correos electrónicos de phishing mediante aprendizaje automático y procesamiento de lenguaje natural.

**Universidad Privada Antenor Orrego (UPAO)**
Facultad de Ingeniería - Escuela de Ingeniería de Computación y Sistemas
Curso: Aprendizaje Estadístico - NRC 4995
Docente: Hernan Sagastegui Chigne
Semestre: 2026-II

**Integrantes:**
- Eustaquio Ávila, Joel Antony
- Marquez Rodriguez, Franco Guillermo
- Velásquez Revilla, Favio Adriano

---

## 1. Documentación del proyecto

### Problema
El phishing es uno de los ataques más comunes por correo electrónico. El atacante se hace pasar por un banco, una empresa o una persona de confianza para robar contraseñas o datos personales. El objetivo del proyecto es clasificar automáticamente un correo como **phishing** o **legítimo** a partir de su texto.

### Data-set
Usamos el data-set "Phishing Email Detection" de Kaggle (subhajournal, 2023):
https://www.kaggle.com/datasets/subhajournal/phishingemails

- 18 650 correos en inglés con dos clases: Safe Email y Phishing Email.
- Después de quitar nulos, vacíos y duplicados quedan 17 536 correos (62.6 % legítimos y 37.4 % phishing).
- El data-set no está en este repositorio porque pesa 52 MB. El Colab lo descarga solo desde Kaggle.

### Modelo
1. **Limpieza del texto:** minúsculas, quitar HTML, cambiar enlaces por "url" y correos por "email", quitar números y signos, quitar stopwords y aplicar stemming (Porter).
2. **TF-IDF:** 5000 términos entre unigramas y bigramas.
3. **6 características estructurales:** número de enlaces, número de caracteres, número de palabras, proporción de mayúsculas, signos de exclamación y palabras de urgencia (urgent, verify, password, etc.).
4. **Regresión logística** con clases balanceadas.
5. División 70 % entrenamiento y 30 % prueba (estratificada) y validación cruzada de 10 pliegues.

Si la probabilidad de phishing es mayor o igual a 0.5, el correo se clasifica como PHISHING; si no, como LEGÍTIMO.

### Resultados principales
Resultados en el conjunto de prueba (5 261 correos):

| Métrica | Resultado | Meta |
|---|---|---|
| Accuracy | 0.9766 | > 0.90 |
| Precision | 0.9633 | > 0.90 |
| Recall | 0.9746 | > 0.90 |
| F1-score | 0.9689 | > 0.90 |
| Tasa de falsos positivos | 0.0222 | < 0.05 |
| AUC | 0.997 | - |

Matriz de confusión: 3221 verdaderos negativos, 73 falsos positivos, 50 falsos negativos y 1917 verdaderos positivos.

### Enlaces
- Informe del proyecto: [docs/Informe_Proyecto_Phishing.pdf](docs/Informe_Proyecto_Phishing.pdf)
- Colab del proyecto: https://colab.research.google.com/drive/1EVCmeimmvzYhb1KEwd6lxX0e0ZgqGwuv?usp=sharing

---

## 2. Código del sistema

| Archivo | Qué hace |
|---|---|
| `app.py` | Aplicación web en Streamlit. Recibe el texto del correo y muestra si es phishing o legítimo. |
| `procesamiento.py` | Funciones de limpieza del texto (`limpiar_texto`) y de las 6 características (`estructurales`), iguales a las del Colab. |
| `modelo_phishing.joblib` | Modelo ya entrenado en el Colab (TF-IDF + características + regresión logística). |
| `requirements.txt` | Librerías con las mismas versiones del Colab. |
| `.streamlit/config.toml` | Colores y tipo de letra de la app. |
| `notebooks/Proyecto_Phishing_Colab.ipynb` | Colab completo: data-set, limpieza, entrenamiento, evaluación y creación de los archivos de la app. |
| `pruebas/prueba_correos_nuevos.py` | Prueba el modelo guardado con 6 correos nuevos. |
| `docs/Informe_Proyecto_Phishing.pdf` | Informe del proyecto. |

---

## 3. Ejecución y pruebas

### Ejecutarlo en una computadora
Se necesita Python 3.13 (la misma versión del Colab).

```
pip install -r requirements.txt
streamlit run app.py
```

Luego se abre en el navegador la dirección que muestra la terminal (normalmente http://localhost:8501).

Para probar el modelo sin abrir la app:

```
python pruebas/prueba_correos_nuevos.py
```

### Prueba con correos nuevos
Probamos el sistema con 6 correos escritos por nosotros, que no están en el data-set:

| Correo | Esperado | Predicho | P(phishing) | ¿Acierta? |
|---|---|---|---|---|
| Hi John, attached is the report for tomorrow's meeting... | LEGÍTIMO | LEGÍTIMO | 0.0180 | Sí |
| Reminder: the team lunch was moved to Friday at 1 pm... | LEGÍTIMO | LEGÍTIMO | 0.1379 | Sí |
| Hello professor, I am sending you the homework for chapter 4... | LEGÍTIMO | PHISHING | 0.7833 | No |
| URGENT: Your account has been suspended! Verify your password... | PHISHING | PHISHING | 0.7797 | Sí |
| Congratulations!!! You have won $1,000,000. Click here... | PHISHING | PHISHING | 0.7846 | Sí |
| Dear customer, we detected unusual activity in your bank account... | PHISHING | PHISHING | 0.8501 | Sí |

El sistema acierta 5 de 6. El correo "Hello professor..." es legítimo pero sale como phishing. Lo dejamos tal cual porque es un resultado real del modelo y muestra una de sus limitaciones.

### Aplicación publicada
La app está publicada en Streamlit Community Cloud: https://detector-phishing-ml.streamlit.app
