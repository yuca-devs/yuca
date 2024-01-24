import functools
import logging
from pathlib import Path

import requests
import typer
from bs4 import BeautifulSoup

from yuca.app_data import AppData
from yuca.data_handlers import load_user_data, save_yaml

data_app = typer.Typer()


def with_query_params(url: str, **params) -> str:
    url += "&" if "?" in url else "?"
    return url + "&".join(f"{k}={v}" for k, v in params.items())


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
    if citations.endswith("*"):
        citations = citations[:-1]
    gray_tags = citation.find_all("div", {"class": "gs_gray"})
    coauthors = gray_tags[0].text
    venue = gray_tags[1].text

    return {
        "title": title,
        "year": int(year) if year else None,
        "venue": venue,
        "citations": int(citations) if citations else 0,
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

    scraped = []
    cstart = 0
    while True:
        curr_page = with_query_params(profile_url, cstart=cstart, pagesize=100)
        new_scraped = get_publications_info(curr_page)
        if not new_scraped:
            break
        scraped += new_scraped
        cstart += 100

    logging.info(f"Found {len(scraped)} publications/preprints from google scholar")

    publ_dict = {e["title"]: e for e in data["publications"]}
    prep_dict = {e["title"]: e for e in data["preprints"]}

    added, updated = 0, 0

    for paper_entry in scraped:
        title = paper_entry["title"]
        is_preprint = "arxiv" in paper_entry["venue"].lower()
        is_an_update = title in publ_dict or title in prep_dict
        is_published_version = not is_preprint and title in prep_dict
        entry_section = prep_dict if is_preprint else publ_dict

        entry_section[title] = paper_entry
        if is_published_version:
            prep_dict.pop(title)
        updated += is_an_update
        added += not is_an_update

    data["publications"] = list(publ_dict.values())
    data["preprints"] = list(prep_dict.values())

    logging.info(f"Added {added} new publications/preprints")
    logging.info(f"Updated {updated} old publications/preprints")
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
