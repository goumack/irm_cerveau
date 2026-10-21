# Image de service du modèle VGG16 (détection de tumeur cérébrale)
# Base UBI Red Hat : compatible avec l'UID arbitraire imposé par OpenShift
FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /opt/app-root/src

# Dépendances d'abord, pour profiter du cache Docker entre deux versions du modèle
COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY app/ app/
COPY vgg16-tumeur/1/model.onnx modele/model.onnx

ENV CHEMIN_MODELE=/opt/app-root/src/modele/model.onnx \
    SEUIL=0.5 \
    VERSION_MODELE=1 \
    THREADS=2 \
    PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.title="vgg16-tumeur" \
      org.opencontainers.image.description="API de détection de tumeur cérébrale sur IRM (VGG16 ONNX)" \
      org.opencontainers.image.authors="Baye Gorgoumack Niang"

USER 1001
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
