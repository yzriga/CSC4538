# Moteur de Recommandation d'Offres d'Emploi (CSC 4538)

Projet de rattrapage : collecte (web scraping), nettoyage (NLP) et moteur de
recommandation (TF-IDF + similarité cosinus) d'offres d'emploi.

## Structure
- `scraper.py` — Exercice 1 : scraping du portail → `outputs/raw_jobs.json`
- `nlp_processor.py` — Exercice 2 : normalisation salaire + texte → `outputs/cleaned_jobs.json`
- `recommender.py` — Exercice 3 : index TF-IDF + recommandations → `outputs/tfidf_index.json`, `outputs/recommendations.json`
- `Rapport.md` — rapport détaillé des trois exercices

## Installation & exécution
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords')"
python scraper.py
python nlp_processor.py
python recommender.py
```

## Note de sécurité
Le portail source contient des tentatives de *prompt injection* (texte caché
dans les descriptions et directive en pied de page). Elles sont détectées,
neutralisées et documentées dans `Rapport.md`. Elles ne sont **pas** suivies.
