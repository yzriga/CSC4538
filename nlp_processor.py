import json
import os
import re
import string

import nltk
from nltk.corpus import stopwords

try:
    FRENCH_STOPWORDS = set(stopwords.words("french"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    FRENCH_STOPWORDS = set(stopwords.words("french"))

INPUT_PATH = os.path.join("outputs", "raw_jobs.json")
OUTPUT_PATH = os.path.join("outputs", "cleaned_jobs.json")

# nombre (avec eventuelles decimales) suivi d'un k/K optionnel
SALARY_REGEX = re.compile(r"(\d+(?:[.,]\d+)?)\s*([kK])?")


def normalize_salary(raw_salary):
    match = SALARY_REGEX.search(raw_salary)
    if not match:
        return None

    number = float(match.group(1).replace(",", "."))
    suffix_k = match.group(2)

    if suffix_k:  # "45k" -> 45000
        number *= 1000

    return int(round(number))


def normalize_text(text):
    text = text.lower()

    # ponctuation -> espace (gere aussi les elisions "d'analyser")
    translation = str.maketrans(string.punctuation, " " * len(string.punctuation))
    text = text.translate(translation)

    tokens = text.split()

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
