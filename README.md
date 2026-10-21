# Détection de tumeurs cérébrales sur IRM (VGG16)

**Auteur :** Baye Gorgoumack Niang · **Projet :** SANTE IA SENIA

Classifieur binaire (tumeur / pas de tumeur) sur des coupes IRM cérébrales, obtenu par transfert d'apprentissage sur VGG16. Le modèle est exporté en ONNX et servi par une API FastAPI conteneurisée, déployée sur OpenShift.

> ⚠️ Projet de recherche : ce n'est pas un dispositif médical, et il ne remplace pas l'avis d'un radiologue.

## Résultats (jeu de test, 38 images)

| Accuracy | AUC ROC | Rappel « tumeur » | Rappel « pas de tumeur » |
|---|---|---|---|
| 0.79 | 0.87 | 0.96 | 0.53 |

Le modèle rate très peu de tumeurs (1 sur 23), mais produit encore des faux positifs. Les pistes d'amélioration sont détaillées dans la conclusion du notebook.

## Organisation

| Chemin | Contenu |
|---|---|
| [`detection-tumeur-cerebrale-vgg16.ipynb`](detection-tumeur-cerebrale-vgg16.ipynb) | données, prétraitement, entraînement en 2 phases, évaluation, export ONNX |
| [`deploiement/`](deploiement/) | API, Dockerfile, manifestes OpenShift, script de déploiement ([README](deploiement/README.md)) |

## Démarche

1. **Données** : [Brain MRI Images for Brain Tumor Detection](https://www.kaggle.com/datasets/navoneel/brain-mri-images-for-brain-tumor-detection) (253 images), téléchargées avec `kagglehub`, puis découpées en train / validation / test de façon stratifiée.
2. **Prétraitement** : recadrage automatique du cerveau (seuillage + plus grand contour), redimensionnement 224×224.
3. **Modèle** : VGG16 ImageNet → GlobalAveragePooling → Dropout → Dense sigmoïde. Augmentation par couches Keras, poids de classe.
4. **Entraînement** : tête seule (VGG16 gelé), puis fine-tuning du bloc 5.
5. **Export** : graphe d'inférence sans augmentation, prétraitement VGG16 inclus, ONNX vérifié identique à Keras.

## Démarrage rapide

```powershell
git clone https://github.com/goumack/irm_cerveau.git
cd irm_cerveau/deploiement
docker build -t vgg16-tumeur:1.0.0 .
docker run -d -p 8090:8080 vgg16-tumeur:1.0.0
# http://localhost:8090/docs
```

Le modèle `deploiement/vgg16-tumeur/1/model.onnx` (59 Mo) est versionné directement dans le dépôt.

## Reproduire l'entraînement

Python 3.10, TensorFlow 2.20, Keras 3, OpenCV, scikit-learn, `kagglehub`, `tf2onnx`, `onnxruntime`. Ouvre le notebook et exécute toutes les cellules. Compte environ 20 minutes sur CPU.

Sous Windows, TensorFlow doit être importé **avant** scikit-learn : la `msvcp140.dll` embarquée par scikit-learn fait sinon échouer le chargement de TensorFlow.
