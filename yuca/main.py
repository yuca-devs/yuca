import os
from pathlib import Path
from typing import Annotated, Optional

import typer

import yuca.generation as gen
from yuca.app_data import AppData
from yuca.data_handlers import load_recipe, load_user_data_from_recipe
from yuca.template.template_app import template_app
from yuca.warehouse.warehouse_app import warehouse_app

app = typer.Typer()
app.add_typer(warehouse_app, name="warehouse")
app.add_typer(template_app, name="template")


def _run_cmd(cmd):
    print(f"Running {cmd}")
    os.system(cmd)


def _handle_cmds(cmds: str | list[str]):
    if isinstance(cmds, str):
        cmds = [cmds]
    for c in cmds:
        _run_cmd(c)


def _resolve_recipe_path(recipe: str) -> str | None:
    recipe_path = Path(recipe)
    if recipe_path.exists():
        return str(recipe_path)

    recipes_folder = Path(AppData.get_default_warehouse()) / "recipes"
    for file in recipes_folder.glob("*.yml"):
        if recipe == file.stem:
            return str(file.resolve())

    return None


@app.command(name="cook")
def generate(
    recipe: str,
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output folder")
    ] = None,
):
    recipe_path = _resolve_recipe_path(recipe)

    if recipe_path is None:
        print(f"Invalid recipe '{recipe}'")
        return

    wh_folder = Path(AppData.get_default_warehouse())
    recipe_data = load_recipe(recipe_path)

    template_folder = wh_folder / "templates" / recipe_data["template"]

    # check if template exist
    if not template_folder.exists():
        print(
            f"There is no '{recipe_data['template']}' in your warehouse\n"
            f"Consider using:\n  yuca template get [{recipe_data['template']}-"
            f"template-url] --name {recipe_data['template']}"
        )
        return

    if output is None:
        output = f"./{Path(recipe_path).stem}-cooked"

    output_folder = Path(output)
    output_folder.mkdir(parents=True, exist_ok=True)

    _handle_cmds(recipe_data.get("pre_cook", []) or [])

    recipe_data["user_data"] = str(wh_folder / "data" / recipe_data["user_data"])
    user_data = load_user_data_from_recipe(recipe_data)

    gen_config = recipe_data.get("gen_config", {}) or {}
    gen_config["static"] = str(wh_folder / "static")

    gen.generate(template_folder, output_folder, gen_config, user_data)

    os.chdir(output_folder)
    _handle_cmds(recipe_data.get("post_cook", []) or [])


def main():
    app()
