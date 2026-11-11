import re
from functools import lru_cache
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

URGENCIA = ["urgent", "verify", "account", "password", "suspend", "confirm",
            "immediately", "bank", "security", "login", "click"]
patron_url = re.compile(r"http\S+|www\.\S+", re.I)
patron_urg = re.compile(r"\b(" + "|".join(URGENCIA) + r")\b", re.I)
stemmer = PorterStemmer()

@lru_cache(maxsize=None)
def raiz(palabra):
    return stemmer.stem(palabra)

def prop_mayus(t):
    letras = sum(c.isalpha() for c in t)
    if letras == 0:
        return 0.0
    return sum(c.isupper() for c in t) / letras

def estructurales(t):
    return {"n_urls": len(patron_url.findall(t)),
            "n_caracteres": len(t),
            "n_palabras": len(t.split()),
            "prop_mayus": prop_mayus(t),
            "n_exclam": t.count("!"),
            "n_urgencia": len(patron_urg.findall(t))}

def limpiar_texto(s):
    s = s.lower()
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"http\S+|www\.\S+", " url ", s)
    s = re.sub(r"\S+@\S+", " email ", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    palabras = [p for p in s.split() if p not in ENGLISH_STOP_WORDS and len(p) > 2]
    return " ".join(raiz(p) for p in palabras)
