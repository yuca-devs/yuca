import os
import shutil
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from git.repo import Repo

from yuca.app_data import AppData

template_app = typer.Typer()


def get_repo_name_from_url(url: str) -> str | None:
    _from = url.rfind("/")
    _to = url.rfind(".git")
    if _to < 0:
        _to = len(url)

    if _from < 0 or _to <= _from:
        return None

    return url[_from + 1 : _to]


def _resolve_git_template(url: str, destination_path: Path):
    Repo.clone_from(url, to_path=str(destination_path), depth=1)

def _copy_base_recipe(template_path: Path):
    wh_folder = Path(AppData.active_warehouse())
    base_recipe = template_path / "base-recipe.yml"
    if base_recipe.exists():
        shutil.copyfile(
            str(base_recipe),
            str(wh_folder / "recipes" / f"{template_path.name}-base-recipe.yml"),
        )

def _resolve_zip_template(url: str, name: str | None):
    raise NotImplementedError()


@template_app.command("get", help="Download a yuca template from a url")
def template_get(url: str, name: Annotated[Optional[str], typer.Option()] = None):
    # Resolve the template name to be used locally
    template_name = get_repo_name_from_url(url) if name is None else name
    if template_name is None:
        logging.error("Invalid url {url}")
        return

    # Go to the templates directory
    templates_folder = Path(AppData.active_warehouse()) / "templates"
    os.chdir(str(templates_folder))

    # Check that there are not other templates with the same name  
    final_template_path = templates_folder / template_name
    if final_template_path.exists():
        logging.error(f"Template '{template_name}' already exists in your active warehouse")
        return
    
    # Download the template depending on the url type 
    if url.endswith(".git"):
        _resolve_git_template(url, final_template_path)
    elif url.endswith(".zip"):
        _resolve_zip_template(url, final_template_path)
    else:
        logging.error(f"Invalid template url: '{url}'")

    # Copy base recipe to the recipes folder of the warehouse
    _copy_base_recipe(final_template_path)