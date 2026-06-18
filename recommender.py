"""
Exercice 3 - Indexation TF-IDF et Recommandation (Similarite Cosinus)

Entree  : outputs/cleaned_jobs.json
Sorties :
    - outputs/tfidf_index.json      (index inverse des poids TF-IDF)
    - outputs/recommendations.json  (Top 3 des offres pour 3 profils)

Definitions retenues :
    tf(t, d)  = nombre d'occurrences de t dans d / nombre total de tokens de d
    df(t)     = nombre de documents contenant t
    idf(t)    = ln( N / df(t) )           (logarithme naturel, N = nb de documents)
    tfidf     = tf(t, d) * idf(t)

Le profil candidat est represente par un vecteur de poids IDF (presence de la
competence ponderee par son IDF). La pertinence d'une offre est mesuree par la
similarite cosinus entre le vecteur du profil et le vecteur TF-IDF de l'offre.
"""

import json
import math
import os
from collections import Counter

INPUT_PATH = os.path.join("outputs", "cleaned_jobs.json")
TFIDF_PATH = os.path.join("outputs", "tfidf_index.json")
RECO_PATH = os.path.join("outputs", "recommendations.json")

PROFILES = {
    "Profil_A": ["python", "sql", "spark", "hadoop", "scala"],
    "Profil_B": ["python", "transformers", "nlp", "pytorch", "regex"],
    "Profil_C": ["python", "django", "api", "git", "bash"],
}


def compute_idf(documents):
    """Calcule l'IDF de chaque token. documents : {id_offre: [tokens]}."""
    n_docs = len(documents)
    df = Counter()
    for tokens in documents.values():
        for token in set(tokens):
            df[token] += 1
    return {token: math.log(n_docs / freq) for token, freq in df.items()}, df


def compute_tfidf_index(documents, idf):
    """Construit l'index inverse : {token: {id_offre: poids_tfidf}}."""
    index = {}
    for id_offre, tokens in documents.items():
        if not tokens:
            continue
        total = len(tokens)
        counts = Counter(tokens)
        for token, count in counts.items():
            tf = count / total
            weight = tf * idf[token]
            index.setdefault(token, {})[id_offre] = round(weight, 6)
    return index


def build_doc_vectors(documents, idf):
    """Renvoie {id_offre: {token: tfidf}} pour le calcul de similarite."""
    vectors = {}
    for id_offre, tokens in documents.items():
        if not tokens:
            vectors[id_offre] = {}
            continue
        total = len(tokens)
        counts = Counter(tokens)
        vectors[id_offre] = {
            token: (count / total) * idf[token]
            for token, count in counts.items()
        }
    return vectors


def build_profile_vector(skills, idf):
    """Represente un profil par un vecteur de poids IDF.

    Une competence absente de l'index (idf inconnu) recoit un poids nul.
    """
    return {skill: idf.get(skill, 0.0) for skill in skills}


def cosine_similarity(vec_a, vec_b):
    """Similarite cosinus entre deux vecteurs creux (dictionnaires)."""
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in common)

    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def recommend(profile_vector, doc_vectors, top_n=3):
    """Renvoie le Top N des offres les plus similaires au profil."""
    scores = []
    for id_offre, doc_vec in doc_vectors.items():
        score = cosine_similarity(profile_vector, doc_vec)
        scores.append((id_offre, score))

    scores.sort(key=lambda pair: pair[1], reverse=True)
    return [
        {"id_offre": id_offre, "score": round(score, 4)}
        for id_offre, score in scores[:top_n]
    ]


def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        cleaned_jobs = json.load(f)

    documents = {job["id_offre"]: job["tokens_description"] for job in cleaned_jobs}

    idf, _df = compute_idf(documents)

    # 1. Index inverse TF-IDF
    tfidf_index = compute_tfidf_index(documents, idf)
    os.makedirs("outputs", exist_ok=True)
    with open(TFIDF_PATH, "w", encoding="utf-8") as f:
        json.dump(tfidf_index, f, ensure_ascii=False, indent=2)
    print(f"Index TF-IDF ({len(tfidf_index)} tokens) sauvegarde dans {TFIDF_PATH}")

    # 2. Moteur de recommandation
    doc_vectors = build_doc_vectors(documents, idf)
    recommendations = {}
    for profile_name, skills in PROFILES.items():
        profile_vector = build_profile_vector(skills, idf)
        recommendations[profile_name] = recommend(profile_vector, doc_vectors)

    with open(RECO_PATH, "w", encoding="utf-8") as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)
    print(f"Recommandations sauvegardees dans {RECO_PATH}")

    for profile_name, reco in recommendations.items():
        print(f"\n{profile_name} :")
        for item in reco:
            print(f"  {item['id_offre']} -> {item['score']}")


if __name__ == "__main__":
    main()
