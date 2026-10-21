"""
Client de test de l'API vgg16-tumeur.

Usage :
    python client.py --url https://vgg16-tumeur-<namespace>.apps.data-ai.heritage.africa --image irm.jpg
    python client.py --url http://localhost:8080 --image irm1.jpg irm2.png
"""
import argparse

import requests

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--url", required=True, help="URL de l'API (Route OpenShift ou localhost)")
parser.add_argument("--image", required=True, nargs="+", help="une ou plusieurs IRM à analyser")
parser.add_argument("--insecure", action="store_true", help="ne pas vérifier le certificat TLS")
args = parser.parse_args()

for chemin in args.image:
    with open(chemin, "rb") as f:
        r = requests.post(f"{args.url.rstrip('/')}/predire", files={"fichier": f},
                          verify=not args.insecure, timeout=60)
    r.raise_for_status()
    res = r.json()
    print(f"{chemin} -> {res['verdict']} (probabilité = {res['probabilite_tumeur']:.3f}, {res['duree_ms']} ms)")
