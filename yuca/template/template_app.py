import os
import shutil
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


def _resolve_git_template(url: str, name: str | None):
    wh_folder = Path(AppData.get_default_warehouse())
    templates_folder = wh_folder / "templates"
    os.chdir(str(templates_folder))

    template_name = get_repo_name_from_url(url) if name is None else name
    if template_name is None:
        print("Invalid url {url}")
        return

    Repo.clone_from(url, to_path=str(templates_folder / template_name), depth=1)

    base_recipe = templates_folder / template_name / "base-recipe.yml"
    if base_recipe.exists():
        shutil.copyfile(
            str(base_recipe),
            str(wh_folder / "recipes" / f"{template_name}-base-recipe.yml"),
        )


def _resolve_zip_template(url: str, name: str | None):
    raise NotImplementedError()


@template_app.command("get", help="Download a yuca template from a url")
def template_get(url: str, name: Annotated[Optional[str], typer.Option()] = None):
    if url.endswith(".git"):
        _resolve_git_template(url, name)
    elif url.endswith(".zip"):
        _resolve_zip_template(url, name)
    else:
        print(f"Invalid template url: '{url}'")
