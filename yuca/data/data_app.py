import functools
import logging
from pathlib import Path

import requests
import typer
from bs4 import BeautifulSoup

from yuca.app_data import AppData
from yuca.data_handlers import load_user_data, save_yaml

data_app = typer.Typer()


def make_google_scholar_profile_html(profile_url) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(profile_url, headers=headers)
    if response.status_code != 200:
        print("Error: Unable to fetch the Google Scholar profile.")
        return ""
    return response.text


def parse_single_publication_info(citation):
    title_element = citation.find("a", {"class": "gsc_a_at"})
    title = title_element.text
    link = "https://scholar.google.com" + title_element["href"]
    year = citation.find("td", {"class": "gsc_a_y"}).text
    citations = citation.find("td", {"class": "gsc_a_c"}).text
    gray_tags = citation.find_all("div", {"class": "gs_gray"})
    coauthors = gray_tags[0].text
    venue = gray_tags[1].text

    return {
        "title": title,
        "year": int(year),
        "venue": venue,
        "citations": int(citations) if citations != '' else 0,
        "coauthors": coauthors,
        "link": link,
    }


def parse_profile_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    publications = []

    for citation in soup.find_all("tr", {"class": "gsc_a_tr"}):
        publication_info = parse_single_publication_info(citation)
        publications.append(publication_info)

    return publications


@functools.lru_cache
def get_publications_info(profile_url) -> list:
    try:
        html = make_google_scholar_profile_html(profile_url)
        return parse_profile_html(html) if html else list()

    except Exception as e:
        print("An error occurred:", e)
        return []


def update_publications(data: dict) -> dict:
    profile_url = data.get("socials", {}).get("googlescholar", None)
    if profile_url is None:
        logging.warning("You dont have socials.googlescholar defined in your data file")
        return data
    publications = get_publications_info(profile_url)
    if len(publications):
        data["publications"] = publications
        logging.info(f"Found {len(publications)} publications from google scholar")
    else:
        logging.warning(f"No publications found in google scholar. Nothing was updated")

    return data


def update_stats(data: dict) -> dict:
    publications_data = data["publications"]
    students_data = data["students"]
    courses_taught_data = data["courses_taught"]

    data["stats"]["publications"] = len(publications_data)
    data["stats"]["citations"] = sum(p["citations"] for p in publications_data)
    data["stats"]["students"] = len(students_data)
    data["stats"]["courses_taught"] = sum(len(c["dates"]) for c in courses_taught_data)

    return data


@data_app.command("update")
def data_update():
    data_folder = Path(AppData.active_warehouse()) / "data"
    for file in data_folder.glob("*.yml"):
        data = load_user_data(str(file))
        logging.info(f"Updating '{file.stem}' data")
        data = update_publications(data)
        data = update_stats(data)
        save_yaml(data, str(file))
