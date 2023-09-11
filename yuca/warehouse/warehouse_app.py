from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from yuca.app_data import AppData
from yuca.data_handlers import load_yaml, save_yaml

warehouse_app = typer.Typer()


@warehouse_app.command(name="init", help="Creates and/or registers a new warehouse")
def warehosue_init(
    path: Annotated[
        str, typer.Argument(help="Path where to create the ware house")
    ] = ".",
    set_current: Annotated[
        bool, typer.Option(help="If true, sets the new warehouse as current")
    ] = False,
):
    main_folder = Path(path).absolute().resolve()

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

    AppData.add_warehouse(main_folder)

    if set_current:
        AppData.switch_to_warehouse(main_folder)


@warehouse_app.command(name="show", help="Shows all of your warehouses")
def warehouse_show():
    current_wh = AppData.instance().current_wh
    warehouses = AppData.instance().warehouses
    print("Warehouses: (* current)")
    for i, wh in enumerate(warehouses):
        current = "*" if i == current_wh else " "
        print(f" {current} {i + 1}. {wh}")


@warehouse_app.command(name="current", help="Shows the path of the current warehouse")
def warehouse_current():
    if not AppData.has_warehouses():
        print(
            "You have not create or register any warehouse",
            "Run 'yuca warehouse init --help' to see hoy to create a warehouse",
            sep="\n",
        )
        return
    print(AppData.get_default_warehouse())


@warehouse_app.command(name="switch", help="Sets a warehouse as current")
def warehosue_set_default(
    path: Annotated[
        Optional[str],
        typer.Argument(
            help="Path of the warehouse to switch to. If not specified, "
            "a list of all of your warehouses will be shown to select one."
        ),
    ] = None
):
    if path is None:
        warehouse_show()
        warehouses = AppData.instance().warehouses
        try:
            idx = int(input("Select a warehouse number: ")) - 1
            if idx < 0 or idx >= len(warehouses):
                raise ValueError()
            path = warehouses[idx]
        except ValueError:
            print("Invalid selection")
            return

    main_folder_path = str(Path(path).absolute().resolve())

    if main_folder_path not in AppData.get_warehouses():
        print(
            f"The folder '{main_folder_path}' is not registered as a yuca warehouse",
            f"Consider useing 'yuca warehouse init {main_folder_path}'",
            sep="\n",
        )
        return

    AppData.switch_to_warehouse(main_folder_path)

    print(f"Switched to warehouse: '{AppData.get_default_warehouse()}'")
