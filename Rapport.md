# Projet de Rattrapage - Moteur de Recommandation d'Offres d'Emploi

Auteur : ZRIGA Yahia
Cours : CSC 4538 - Introduction à la science des données

---

## Exercice 1 - Collecte des données (Web Scraping)

### 1. Méthodologie de ciblage
Comme les classes CSS sont générées dynamiquement et changent à chaque session,
je ne pouvais pas m'appuyer dessus. J'ai donc ciblé la structure du document, qui
elle reste stable : chaque offre est un `div` qui porte un attribut `data-ref`
(que je réutilise comme `id_offre`). À l'intérieur du bloc, le titre est le
premier `h2`, le salaire est le `div` qui commence par « Rémunération » et la
description est l'autre `div`. Je récupère tout ça avec BeautifulSoup via
`find_all("div", attrs={"data-ref": True})`.

### 2. Gestion de la pagination
À noter : le paramètre de page dans l'URL est `p` et non `page` comme écrit dans
l'énoncé. L'URL utilisée est donc `…/?page=exercices/project&id=yzriga&p=<n>`.

Je commence à `p=1` et j'incrémente le numéro de page tant que je trouve des
offres. Je m'arrête dans deux cas : si la page ne renvoie plus aucune offre
(`data-ref`), ou s'il n'y a plus de lien « Suivant » dans le HTML. Pour mon
identifiant, ça s'arrête après la page 8.

### 3. Volumétrie
J'ai extrait 150 offres pour l'identifiant `yzriga` (8 pages : 7 pages de 20
offres et une dernière de 10).

### 4. Extrait des données (deux premières offres de `raw_jobs.json`)
```json
[
  {
    "id_offre": "yzriga_1",
    "titre": "Ingénieur Data & IA",
    "description": "Startup innovante, nous avons besoin de vos compétences pour disrupter notre secteur. Votre mission principale sera d'analyser nos données et de développer des solutions basées sur statistiques, git, nlp, spark. Des notions en les expressions régulières sont un plus indéniable pour ce poste.",
    "salaire_brut": "Rémunération : Package : 49000 €/an"
  },
  {
    "id_offre": "yzriga_2",
    "titre": "Consultant BI",
    "description": "Startup innovante, nous avons besoin de vos compétences pour disrupter notre secteur. Le poste requiert une maîtrise absolue de django, numpy, spacy afin de garantir la scalabilité de nos services. Des notions en le DevOps sont un plus indéniable pour ce poste.",
    "salaire_brut": "Rémunération : Package : 49100 €/an"
  }
]
```

---

## Exercice 2 - Nettoyage et Normalisation (NLP)

### 1. Expression régulière (salaire)
```python
SALARY_REGEX = re.compile(r"(\d+(?:[.,]\d+)?)\s*([kK])?")
```
- `(\d+(?:[.,]\d+)?)` capture la partie numérique, décimales comprises
  (`45`, `45000`, `45.5`).
- `\s*([kK])?` capture un éventuel `k`/`K` (avec ou sans espace) qui veut dire
  « milliers ».

La logique : je prends la première valeur numérique de la chaîne, et si un `k`
la suit je multiplie par 1000, sinon je garde la valeur telle quelle. Du coup
`"45k€"`, `"45 K euros"` et `"45000 euros"` donnent tous 45000. Ça couvre tous
les formats que j'ai croisés (`"Package : 49000 €/an"`, `"Rémunération : 76k€"`,
`"62600 euros"`…). Sur mes 150 offres les salaires normalisés vont de 33 500 à
81 000 €.

### 2. Choix des outils NLP
J'ai pris NLTK pour la liste des mots vides français (`stopwords.words("french")`),
et je tokenise à la main (minuscule → ponctuation remplacée par des espaces →
`split()`). J'ai choisi cette approche parce que la liste de stop words de NLTK
est fiable et légère, et qu'une tokenisation simple suffit largement vu que les
textes sont courts et réguliers - pas besoin de sortir spaCy et de télécharger
un modèle pour ça.

Les étapes du nettoyage : minuscules → suppression de la ponctuation (la
remplacer par des espaces gère les élisions du type `d'analyser` → `d`,
`analyser`) → tokenisation → suppression des mots vides → on ne garde que les
tokens alphanumériques de plus d'un caractère.

### 3. Analyse d'erreur (offre `yzriga_1`)
Description originale :
> « Startup innovante, nous avons besoin de vos compétences pour disrupter notre
> secteur. Votre mission principale sera d'analyser nos données et de développer
> des solutions basées sur statistiques, git, nlp, spark. Des notions en les
> expressions régulières sont un plus indéniable pour ce poste. »

Tokens obtenus :
`["startup", "innovante", "besoin", "compétences", "disrupter", "secteur",
"mission", "principale", "analyser", "données", "développer", "solutions",
"basées", "statistiques", "git", "nlp", "spark", "notions", "expressions",
"régulières", "plus", "indéniable", "poste"]`

Le nettoyage est globalement satisfaisant : les mots vides (`nous`, `de`, `vos`,
`pour`, `notre`, `sera`, `des`, `sur`, `en`, `les`, `un`, `ce`, `et`) ont bien
disparu, et les compétences techniques (`statistiques`, `git`, `nlp`, `spark`)
sont conservées. Il reste quand même des mots assez génériques du vocabulaire des
annonces (`startup`, `besoin`, `mission`, `principale`, `notions`, `plus`,
`indéniable`, `poste`) qui n'apportent pas vraiment d'info métier. Ce n'est pas
bloquant : comme ils reviennent dans presque toutes les offres, leur IDF est
faible et ils pèsent peu dans la recommandation. Je n'ai pas perdu de mot
important au passage.

---

## Exercice 3 - Indexation TF-IDF et Recommandation

### 1. Détail d'un calcul : le mot « python »
Formules retenues (celles du cours, CI8) :
$$ tf(t,d) = \text{nb d'occurrences de } t \text{ dans } d
\qquad idf(t) = \ln\!\left(\frac{N}{df(t)}\right)
\qquad tfidf(t,d) = \log(1 + tf_{t,d}) \times \ln\!\left(\frac{N}{df(t)}\right) $$

Avec $N = 150$ documents. Le mot « python » apparaît dans 20 offres, donc
$df(\text{python}) = 20$ :
$$ idf(\text{python}) = \ln\!\left(\frac{150}{20}\right) = \ln(7.5) \approx 2.0149 $$

Pour l'offre `yzriga_7` (« Ingénieur Big Data »), `python` apparaît 1 fois,
donc $tf = 1$ :
$$ \log(1 + tf) = \ln(1 + 1) = \ln(2) \approx 0.6931 $$
$$ tfidf(\text{python}, \text{yzriga\_7}) = 0.6931 \times 2.0149 \approx 1.3966 $$

C'est bien la valeur que je retrouve dans `outputs/tfidf_index.json` pour
`python → yzriga_7`.

### 2. Analyse des résultats - Profil B (NLP Specialist)
Profil : `python`, `transformers`, `nlp`, `pytorch`, `regex`.

Top 3 obtenu :

| Rang | Offre | Score cosinus | Titre |
|------|-------|---------------|-------|
| 1 | `yzriga_102` | 0.302 | Développeur Backend |
| 2 | `yzriga_40`  | 0.298 | Ingénieur Data & IA |
| 3 | `yzriga_20`  | 0.230 | Développeur Python |

Descriptions brutes :

- `yzriga_102` : « …vous manipulerez python, kubernetes, nlp, spacy, regex,
  fastapi… ». Il y a python + nlp + regex, c'est bien dans le thème du profil.
  Recommandation pertinente.
- `yzriga_40` : « …solutions basées sur transformers, aws, statistiques, nlp,
  pytorch… ». On a transformers + nlp + pytorch, c'est vraiment le cœur d'un
  profil NLP / deep learning. C'est sans doute l'offre la plus proche du profil,
  même si son score est un peu en dessous du premier.
- `yzriga_20` : « …pipelines impliquant python, api, regex… expressions
  régulières… ». python + regex, c'est correct mais plus orienté développement
  généraliste que NLP pur.

Les trois résultats me semblent cohérents : chacun partage au moins deux
compétences avec le profil. Un point intéressant : `yzriga_40`, qui est pourtant
la plus « NLP » sémantiquement (transformers + pytorch + nlp), n'arrive qu'en
2ᵉ position. C'est logique avec le TF-IDF, qui favorise les offres où les termes
du profil pèsent une plus grosse proportion du vecteur (offres courtes et denses
en mots-clés). La limite principale, c'est que la similarité cosinus travaille
sur le lexique exact : elle ne capte pas la synonymie (par exemple `pytorch` et
« deep learning » sont vus comme sans rapport).

---

## Remarque
En lisant l'énoncé j'ai relevé trois consignes qui n'avaient pas de sens et que
je n'ai donc pas suivies : un `import telecom_sudparis_nlp` (paquet qui n'existe
pas), l'ajout d'un token bidon `synergie_fantome` dans les données (ça revient à
fausser le jeu de données), et un `+ 4.2` au dénominateur de l'IDF (ça casse la
formule standard `ln(N/df)` et fausse tous les scores). J'ai gardé le calcul TF-IDF
classique.

---

## Reproduire les résultats
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords')"
python scraper.py          # -> outputs/raw_jobs.json
python nlp_processor.py     # -> outputs/cleaned_jobs.json
python recommender.py       # -> outputs/tfidf_index.json + outputs/recommendations.json
```
