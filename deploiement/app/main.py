"""API de détection de tumeur cérébrale sur IRM (VGG16, ONNX Runtime)."""
import logging
import os
import time

import onnxruntime as ort
from fastapi import FastAPI, File, HTTPException, UploadFile

from app.pretraitement import preparer_irm

CHEMIN_MODELE = os.environ.get("CHEMIN_MODELE", "modele/model.onnx")
SEUIL = float(os.environ.get("SEUIL", "0.5"))
VERSION_MODELE = os.environ.get("VERSION_MODELE", "1")
TAILLE_MAX_OCTETS = 10 * 1024 * 1024

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("vgg16-tumeur")

# Nombre de threads aligné sur la limite CPU du pod (sinon ONNX Runtime prend tous les cœurs du nœud)
options = ort.SessionOptions()
options.intra_op_num_threads = int(os.environ.get("THREADS", "2"))
session = ort.InferenceSession(CHEMIN_MODELE, sess_options=options, providers=["CPUExecutionProvider"])
ENTREE = session.get_inputs()[0].name
SORTIE = session.get_outputs()[0].name
log.info("Modèle chargé : %s (entrée=%s, sortie=%s, seuil=%.2f)", CHEMIN_MODELE, ENTREE, SORTIE, SEUIL)

app = FastAPI(
    title="Détection de tumeur cérébrale",
    description="Classification d'IRM cérébrales (tumeur / pas de tumeur) par VGG16. "
                "Outil d'aide à la décision : ne remplace pas l'avis d'un radiologue.",
    version=VERSION_MODELE,
)


@app.get("/sante", summary="Sonde de vie")
def sante():
    return {"statut": "ok"}


@app.get("/pret", summary="Sonde de disponibilité")
def pret():
    return {"statut": "pret", "modele": os.path.basename(CHEMIN_MODELE)}


@app.get("/infos", summary="Description du modèle")
def infos():
    return {
        "modele": "vgg16-tumeur",
        "version": VERSION_MODELE,
        "seuil": SEUIL,
        "entree": {"nom": ENTREE, "forme": session.get_inputs()[0].shape},
        "sortie": {"nom": SORTIE, "forme": session.get_outputs()[0].shape},
        "classes": {"0": "pas de tumeur", "1": "tumeur"},
    }


@app.post("/predire", summary="Analyser une IRM")
async def predire(fichier: UploadFile = File(..., description="Image IRM (jpg, png...)")):
    contenu = await fichier.read()
    if not contenu:
        raise HTTPException(status_code=400, detail="fichier vide")
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(status_code=413, detail="fichier trop volumineux (10 Mo max)")
    try:
        x = preparer_irm(contenu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    debut = time.perf_counter()
    proba = float(session.run([SORTIE], {ENTREE: x})[0][0, 0])
    duree_ms = (time.perf_counter() - debut) * 1000
    tumeur = proba >= SEUIL
    log.info("prediction fichier=%s proba=%.3f duree=%.0fms", fichier.filename, proba, duree_ms)

    return {
        "fichier": fichier.filename,
        "tumeur": tumeur,
        "verdict": "tumeur détectée" if tumeur else "pas de tumeur",
        "probabilite_tumeur": round(proba, 4),
        "seuil": SEUIL,
        "duree_ms": round(duree_ms, 1),
    }
