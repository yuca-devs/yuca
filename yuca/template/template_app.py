import logging
import shutil
from pathlib import Path
from typing import Annotated, Optional

import typer
from git.repo import Repo

from yuca.app_data import AppData

template_app = typer.Typer()


def get_name_from_url(url: str, ending: str = ".git") -> str | None:
    _from = url.rfind("/")
    _to = url.rfind(ending)
    if _to < 0:
        _to = len(url)

    if _from < 0 or _to <= _from:
        return None

    return url[_from + 1 : _to]


def _resolve_git_template(url: str, destination_path: Path):
    Repo.clone_from(url, to_path=str(destination_path), depth=1)


def _resolve_local_template(path: Path, destination_path: Path):
    shutil.copytree(str(path), str(destination_path))


def _resolve_zip_template(url: str, name: str | None):
    raise NotImplementedError()


def _copy_base_recipe(template_path: Path, recipe_name: str):
    recipe_name = recipe_name if recipe_name.endswith(".yml") else f"{recipe_name}.yml"
    wh_folder = Path(AppData.active_warehouse())
    base_recipe = template_path / "base-recipe.yml"
    if base_recipe.exists():
        shutil.copyfile(
            str(base_recipe),
            str(wh_folder / "recipes" / recipe_name),
        )


def _update_git_template(template_path: Path):
    template_repo = Repo(template_path)
    template_repo.git.pull()


def _template_full_path(template_name: str):
    templates_folder = Path(AppData.active_warehouse()) / "templates"
    return templates_folder / template_name


def _resolve_template_name_by_location(location: str) -> str | None:
    loc_path = Path(location)
    name = None
    if loc_path.exists():
        name = loc_path.stem
    elif location.endswith((".git", ".zip")):
        name = get_name_from_url(location)
        if name is None:
            logging.error("Invalid url {url}")
    return name


@template_app.command("update", help="Update an existing yuca template")
def template_update(template_name: str):
    # Resolve the template full path
    final_template_path = _template_full_path(template_name)
    if not final_template_path.exists():
        logging.error(
            f"Template '{template_name}' doesn't exists in your active warehouse"
        )
        return
    template_content = [element.name for element in final_template_path.iterdir()]
    if ".git" in template_content:
        _update_git_template(final_template_path)
    else:
        logging.error(f"Template: '{template_name}' has no update mechanism")


@template_app.command("get", help="Download a yuca template from a url")
def template_get(
    location: Annotated[
        str,
        typer.Argument(
            help="Template location. Can be a local path, a github repository "
            "url, or a url to a zip file."
        ),
    ],
    name: Annotated[
        Optional[str],
        typer.Option(
            help="Name that will have the template in your warehouse. "
            "If not provided, it will be deducted from the location"
        ),
    ] = None,
    base_recipe: Annotated[
        Optional[str],
        typer.Option(
            help="If the template provides a base recipe, when using "
            "this option the template's base recipe will be copied to "
            "your active warehouse recipes folder with the provided name"
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Override the template if it already exists"
        ),
    ] = False,
):
    # Resolve the template name to be used locally
    template_name = (
        _resolve_template_name_by_location(location) if name is None else name
    )
    if template_name is None:
        return

    # Check that there are not other templates with the same name
    final_template_path = _template_full_path(template_name)
    if final_template_path.exists():
        if not force:
            logging.error(
                f"Template '{template_name}' already exists in your active warehouse"
            )
            return
        shutil.rmtree(final_template_path)

    # Download the template depending on the url type
    loc_path = Path(location)
    if loc_path.exists():
        _resolve_local_template(loc_path, final_template_path)
    elif location.endswith(".git"):
        _resolve_git_template(location, final_template_path)
    elif location.endswith(".zip"):
        _resolve_zip_template(location, final_template_path)
    else:
        logging.error(f"Invalid template url: '{location}'")

    # Copy base recipe to the recipes folder of the warehouse
    if base_recipe is not None:
        _copy_base_recipe(final_template_path, base_recipe)
