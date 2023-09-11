from pathlib import Path

import typer
from typing_extensions import Annotated

from yuca.app_data import AppData
from yuca.data_handlers import load_yaml, save_yaml

warehouse_app = typer.Typer()


@warehouse_app.command(name="init", help="Creates and registers a new warehouse")
def warehosue_init(path: Annotated[str, typer.Argument()] = "."):
    main_folder = Path(path)

    data_folder = main_folder / "data"
    templates_folder = main_folder / "templates"
    static_folder = main_folder / "static"
    recipes_folder = main_folder / "recipes"

    data_folder.mkdir(parents=True, exist_ok=True)
    templates_folder.mkdir(parents=True, exist_ok=True)
    static_folder.mkdir(parents=True, exist_ok=True)
    recipes_folder.mkdir(parents=True, exist_ok=True)

    example_user_data = load_yaml(str(Path(__file__).parent / "example_user_data.yml"))
    user_data_file = data_folder / "en.yml"
    if not user_data_file.exists():
        save_yaml(example_user_data, str(user_data_file))

    AppData.add_warehouse(main_folder.absolute())


@warehouse_app.command(name="set-default", help="Sets a warehouse as default")
def warehosue_set_default(path: Annotated[str, typer.Argument()] = "."):
    main_folder_path = str(Path(path).absolute().resolve())

    if main_folder_path not in AppData.get_warehouses():
        print(
            f"The folder '{main_folder_path}' is not registered as a yuca warehouse",
            f"Consider useing 'yuca warehouse init {main_folder_path}'",
            sep="\n",
        )
        return
    AppData.set_default_warehouse(main_folder_path)
