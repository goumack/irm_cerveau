# Déploiement de l'API vgg16-tumeur sur OpenShift

Stratégie : le modèle ONNX est **embarqué dans une image Docker** avec une API FastAPI. L'image est **construite dans le cluster** (BuildConfig binaire, stratégie Docker), puis stockée dans le registre intégré d'OpenShift. Elle est ensuite déployée via un Deployment, un Service et une Route.

L'API fait tout le traitement côté serveur : décodage de l'image, recadrage du cerveau, redimensionnement, puis inférence ONNX Runtime. Le client envoie simplement le fichier IRM.

```
PC  ──oc start-build --from-dir──▶  BuildConfig (Dockerfile)  ──▶  ImageStream vgg16-tumeur
                                                                         │
                                         Route https ◀── Service ◀── Deployment (pod API)
```

## Contenu

| Fichier | Rôle |
|---|---|
| `vgg16-tumeur/1/model.onnx` | modèle exporté par le notebook (59 Mo) |
| `app/main.py` | API FastAPI |
| `app/pretraitement.py` | recadrage du cerveau et redimensionnement, identiques à l'entraînement |
| `app/requirements.txt` | dépendances Python, versions figées |
| `Dockerfile`, `.dockerignore` | image basée sur UBI 9 / Python 3.11, utilisateur non-root |
| `openshift/vgg16-tumeur.yaml` | Deployment, Service et Route (TLS edge) |
| `build-deployer.ps1` | build dans le cluster, tag de version et déploiement en une commande |
| `client.py` | client de test |

## API

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/predire` | analyse une IRM (champ multipart `fichier`) |
| `GET` | `/infos` | description du modèle (entrées, sorties, seuil) |
| `GET` | `/sante` | sonde de vie (liveness) |
| `GET` | `/pret` | sonde de disponibilité (readiness) |
| `GET` | `/docs` | documentation interactive Swagger |

Exemple de réponse de `/predire` :

```json
{"fichier": "Y39.jpg", "tumeur": true, "verdict": "tumeur détectée",
 "probabilite_tumeur": 0.9998, "seuil": 0.5, "duree_ms": 158.2}
```

Variables d'environnement : `SEUIL` (0.5 par défaut), `THREADS` (threads ONNX Runtime, à aligner sur la limite CPU), `VERSION_MODELE`.

## 1. Tester en local avec Docker Desktop

```powershell
cd deploiement
docker build -t vgg16-tumeur:1.0.0 .
docker run -d --name vgg16 -p 8090:8080 --user 1000680000:0 vgg16-tumeur:1.0.0   # UID arbitraire, comme OpenShift
python client.py --url http://localhost:8090 --image chemin\vers\irm.jpg
docker rm -f vgg16
```

## 2. Déployer sur OpenShift

```powershell
oc login --token=sha256~... --server=https://api.origins.heritage.africa:6443
cd deploiement
.\build-deployer.ps1 -Version 1.0.0
```

Étapes manuelles équivalentes :

```powershell
oc project senia-surveillance-gpu
oc new-build --name=vgg16-tumeur --strategy=docker --binary --to=vgg16-tumeur:latest   # une seule fois
oc start-build vgg16-tumeur --from-dir=. --follow
oc tag vgg16-tumeur:latest vgg16-tumeur:1.0.0
oc apply -f openshift/vgg16-tumeur.yaml
oc rollout status deployment/vgg16-tumeur
```

L'image vit dans le même namespace que le pod : aucun secret de pull n'est nécessaire.

## 3. Nouvelle version

```powershell
.\build-deployer.ps1 -Version 1.0.1
```

Le rollout se fait sans coupure (`maxUnavailable: 0`). Pour revenir en arrière : `oc rollout undo deployment/vgg16-tumeur`.

## 4. Vérifier

```powershell
$hote = oc get route vgg16-tumeur -o jsonpath="{.spec.host}"
curl.exe -k "https://$hote/infos"
python client.py --url "https://$hote" --image irm.jpg --insecure
```

## Mesures en local

Conteneur limité à 2 CPU :

| | |
|---|---|
| Taille de l'image | 1,5 Go (dont ~1 Go pour l'image de base UBI Python) |
| Mémoire, modèle chargé | ~200 Mo |
| Temps d'inférence | ~160 ms par IRM |

## Dépannage

| Symptôme | Piste |
|---|---|
| `oc tag` : *not currently pointing to an image* | le build n'est pas terminé : `oc get builds` |
| Build très long ou en timeout | téléchargement lent de l'image de base ou de PyPI depuis le cluster : `oc logs -f build/vgg16-tumeur-N` |
| Pod `ImagePullBackOff` | nom du namespace ou tag incorrect dans l'image du Deployment |
| Pod `OOMKilled` | augmenter `limits.memory` |
| Réponses lentes | aligner `THREADS` sur `limits.cpu`, ou augmenter `replicas` |
| Logs | `oc logs deploy/vgg16-tumeur -f` |
