"""Prétraitement des IRM, identique à celui utilisé pendant l'entraînement du modèle."""
import cv2
import numpy as np

TAILLE_IMG = (224, 224)


def decoder_image(contenu: bytes) -> np.ndarray:
    """Décode un fichier image (jpg, png...) en tableau RGB."""
    img = cv2.imdecode(np.frombuffer(contenu, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("fichier image illisible")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def recadrer_cerveau(img_rgb: np.ndarray, seuil: int = 45) -> np.ndarray:
    """Recadre l'image sur le plus grand contour (le crâne) ; renvoie l'image intacte si rien n'est trouvé."""
    gris = cv2.GaussianBlur(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY), (5, 5), 0)
    masque = cv2.threshold(gris, seuil, 255, cv2.THRESH_BINARY)[1]
    masque = cv2.dilate(cv2.erode(masque, None, iterations=2), None, iterations=2)
    contours, _ = cv2.findContours(masque, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img_rgb
    c = max(contours, key=cv2.contourArea)
    x0, x1 = c[:, :, 0].min(), c[:, :, 0].max()
    y0, y1 = c[:, :, 1].min(), c[:, :, 1].max()
    return img_rgb[y0:y1, x0:x1]


def preparer_irm(contenu: bytes) -> np.ndarray:
    """Fichier brut -> tenseur float32 [1, 224, 224, 3] (pixels 0-255) attendu par le modèle ONNX."""
    img = recadrer_cerveau(decoder_image(contenu))
    img = cv2.resize(img, TAILLE_IMG, interpolation=cv2.INTER_CUBIC)
    return img.astype("float32")[None, ...]
