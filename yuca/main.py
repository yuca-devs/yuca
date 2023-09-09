import os
from pathlib import Path
from typing import Optional

import typer

import yuca.generation as gen
from yuca.data_handlers import load_recipe, load_user_data_from_recipe

app = typer.Typer()


def _run_cmd(cmd):
    print(f"Running {cmd}")
    os.system(cmd)


def _handle_cmds(cmds: str | list[str]):
    if isinstance(cmds, str):
        cmds = [cmds]
    for c in cmds:
        _run_cmd(c)


def _resolve_template(url: str):
    print(f"Resolving template from: {url}")
    raise NotImplementedError()


@app.command(name="sync")
def sync():
    raise NotImplementedError()


@app.command(name="cook")
def generate(recipe_path: str, sync_from: Optional[str] = None):
    recipe = load_recipe(recipe_path)

    recipe_folder = Path(recipe_path).parent
    template_folder = recipe_folder / Path(
        recipe["template_folder"], recipe["template_name"]
    )
    print(template_folder)

    if sync_from is not None:
        _resolve_template(sync_from)

    # check if template exist
    if not template_folder.exists():
        print(
            f"There is no '{recipe['template_name']}' template in '{recipe['template_folder']}'\n"
            f"Consider using --sync-from [template-url]"
        )
        return

    output_folder = recipe_folder / Path(recipe["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    _handle_cmds(recipe.get("pre_cook", []) or [])

    recipe["user_data"] = str(recipe_folder / recipe["user_data"])
    user_data = load_user_data_from_recipe(recipe)

    gen_config = recipe.get("gen_config", {}) or {}
    gen_config["root"] = str(recipe_folder)

    gen.generate(template_folder, output_folder, gen_config, user_data)

    os.chdir(output_folder)
    _handle_cmds(recipe.get("post_cook", []) or [])


def main():
    app()
