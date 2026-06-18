"""
Exercice 2 - Nettoyage et Normalisation des Donnees (NLP)

Entree  : outputs/raw_jobs.json
Sortie  : outputs/cleaned_jobs.json

Deux traitements sont realises :
    1. Normalisation du salaire (expressions regulieres) -> entier annuel brut
    2. Normalisation du texte (minuscule, ponctuation, tokenisation,
       suppression des mots vides francais, tokens alphanumeriques uniquement)
"""

import json
import os
import re
import string

import nltk
from nltk.corpus import stopwords

# Telechargement (silencieux) de la liste des mots vides si necessaire.
try:
    FRENCH_STOPWORDS = set(stopwords.words("french"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    FRENCH_STOPWORDS = set(stopwords.words("french"))

INPUT_PATH = os.path.join("outputs", "raw_jobs.json")
OUTPUT_PATH = os.path.join("outputs", "cleaned_jobs.json")

# Expression reguliere capturant un nombre suivi eventuellement d'un 'k'/'K'.
#   - groupe 1 : la partie numerique (ex: 45, 45000, 45.5)
#   - groupe 2 : un eventuel 'k' (signifiant "milliers")
SALARY_REGEX = re.compile(r"(\d+(?:[.,]\d+)?)\s*([kK])?")


def normalize_salary(raw_salary):
    """Convertit une chaine de salaire libre en entier annuel brut.

    Exemples :
        "45k€"               -> 45000
        "45000 euros"        -> 45000
        "45 K euros"         -> 45000
        "Remuneration : 45000 EUR" -> 45000
        "Package : 49000 €/an"     -> 49000
    """
    match = SALARY_REGEX.search(raw_salary)
    if not match:
        return None

    number = float(match.group(1).replace(",", "."))
    suffix_k = match.group(2)

    # Un 'k' multiplie par 1000 ; sinon la valeur est deja un salaire complet.
    if suffix_k:
        number *= 1000

    return int(round(number))


def normalize_text(text):
    """Nettoie une description et renvoie la liste de tokens normalises."""
    # 1. Minuscules
    text = text.lower()

    # 2. Suppression de la ponctuation (remplacee par des espaces pour gerer
    #    les elisions du type "d'analyser" -> "d analyser").
    translation = str.maketrans(string.punctuation, " " * len(string.punctuation))
    text = text.translate(translation)

    # 3. Tokenisation
    tokens = text.split()

    # 4. Filtrage : on conserve les tokens alphanumeriques, non vides,
    #    de plus d'un caractere et qui ne sont pas des mots vides.
    cleaned = [
        token for token in tokens
        if token.isalnum()
        and len(token) > 1
        and token not in FRENCH_STOPWORDS
    ]

    return cleaned


def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        raw_jobs = json.load(f)

    cleaned_jobs = []
    for job in raw_jobs:
        cleaned_jobs.append({
            "id_offre": job["id_offre"],
            "titre": job["titre"],
            "salaire_num": normalize_salary(job["salaire_brut"]),
            "tokens_description": normalize_text(job["description"]),
        })

    os.makedirs("outputs", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_jobs, f, ensure_ascii=False, indent=2)

    print(f"{len(cleaned_jobs)} offres nettoyees et sauvegardees dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
