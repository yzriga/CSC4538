"""
Exercice 1 - Collecte des donnees (Web Scraping)

Ce script parcourt le portail de recrutement interne et extrait, pour chaque
offre d'emploi :
    - l'identifiant de l'offre (attribut data-ref)
    - le titre du poste
    - la description brute du poste
    - la chaine de caracteres contenant la remuneration

Le resultat est sauvegarde dans outputs/raw_jobs.json.

Particularite du portail : les noms des classes CSS sont generes
dynamiquement et changent a chaque session. On ne peut donc PAS cibler les
elements via leur classe. On s'appuie a la place sur la structure du document :
chaque offre est un <div> portant un attribut "data-ref".
"""

import json
import os
import time

import requests
from bs4 import BeautifulSoup

# --- Configuration --------------------------------------------------------
BASE_URL = "https://www-inf.telecom-sudparis.eu/COURS/CSC4538/Supports/"
STUDENT_ID = "yzriga"          # identifiant Telecom (parametre id)
PAGE_PARAM = "p"               # NB : le parametre de page est 'p' (et non 'page')
OUTPUT_PATH = os.path.join("outputs", "raw_jobs.json")


def fetch_page(page_number):
    """Telecharge une page du portail et renvoie son contenu HTML."""
    params = {
        "page": "exercices/project",
        "id": STUDENT_ID,
        PAGE_PARAM: page_number,
    }
    response = requests.get(BASE_URL, params=params, timeout=20)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def clean_description(content_div):
    """Renvoie la description brute du poste.

    On ignore les <span> non visibles (taille de 1px ou opacite quasi nulle)
    qui ne font pas partie du texte affiche de l'offre.
    """
    for span in content_div.find_all("span"):
        style = span.get("style", "")
        if "1px" in style or "opacity" in style:
            span.decompose()
    return content_div.get_text(separator=" ", strip=True)


def parse_offers(html):
    """Extrait toutes les offres presentes sur une page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    # Chaque offre est un div possedant l'attribut data-ref.
    for box in soup.find_all("div", attrs={"data-ref": True}):
        id_offre = box["data-ref"]

        # Le titre est le premier <h2> du bloc.
        titre_tag = box.find("h2")
        titre = titre_tag.get_text(strip=True) if titre_tag else ""

        # Les blocs internes sont des <div>. Celui qui contient "Remuneration"
        # est le salaire ; l'autre est la description.
        description = ""
        salaire_brut = ""
        for div in box.find_all("div"):
            texte = div.get_text(separator=" ", strip=True)
            if texte.startswith("R") and "mun" in texte:  # "Remuneration : ..."
                salaire_brut = texte
            else:
                description = clean_description(div)

        offers.append({
            "id_offre": id_offre,
            "titre": titre,
            "description": description,
            "salaire_brut": salaire_brut,
        })

    return offers


def has_next_page(html):
    """Indique si un lien 'Suivant' est present (pagination non terminee)."""
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a"):
        if link.get_text(strip=True).lower() == "suivant":
            return True
    return False


def scrape_all():
    """Parcourt toutes les pages jusqu'a epuisement des offres."""
    all_offers = []
    page = 1

    while True:
        print(f"Recuperation de la page {page}...")
        html = fetch_page(page)
        offers = parse_offers(html)

        # Condition d'arret : une page sans aucune offre signifie qu'il n'y a
        # plus de donnees a collecter.
        if not offers:
            print("Aucune offre trouvee : fin de la pagination.")
            break

        all_offers.extend(offers)

        # On s'arrete egalement s'il n'existe plus de lien "Suivant".
        if not has_next_page(html):
            print("Plus de lien 'Suivant' : fin de la pagination.")
            break

        page += 1
        time.sleep(0.3)  # politesse vis-a-vis du serveur

    return all_offers


def main():
    os.makedirs("outputs", exist_ok=True)
    offers = scrape_all()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

    print(f"\n{len(offers)} offres extraites et sauvegardees dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
