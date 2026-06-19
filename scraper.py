import json
import os
import time

import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://www-inf.telecom-sudparis.eu/COURS/CSC4538/Supports/"
STUDENT_ID = "yzriga"
PAGE_PARAM = "p"  # le parametre de page est p
OUTPUT_PATH = os.path.join("outputs", "raw_jobs.json")


def fetch_page(page_number):
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
    # on retire les span non visibles (1px / opacite tres faible)
    for span in content_div.find_all("span"):
        style = span.get("style", "")
        if "1px" in style or "opacity" in style:
            span.decompose()
    return content_div.get_text(separator=" ", strip=True)


def parse_offers(html):
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    for box in soup.find_all("div", attrs={"data-ref": True}):
        id_offre = box["data-ref"]

        titre_tag = box.find("h2")
        titre = titre_tag.get_text(strip=True) if titre_tag else ""

        description = ""
        salaire_brut = ""
        for div in box.find_all("div"):
            texte = div.get_text(separator=" ", strip=True)
            if texte.startswith("R") and "mun" in texte:
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
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a"):
        if link.get_text(strip=True).lower() == "suivant":
            return True
    return False


def scrape_all():
    all_offers = []
    page = 1

    while True:
        print(f"Recuperation de la page {page}...")
        html = fetch_page(page)
        offers = parse_offers(html)

        # une page vide => plus rien a recuperer
        if not offers:
            break

        all_offers.extend(offers)

        # plus de lien "Suivant" => derniere page
        if not has_next_page(html):
            break

        page += 1
        time.sleep(0.3)

    return all_offers


def main():
    os.makedirs("outputs", exist_ok=True)
    offers = scrape_all()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

    print(f"{len(offers)} offres extraites -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
