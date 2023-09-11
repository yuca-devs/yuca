from __future__ import annotations

from pathlib import Path

import platformdirs

from yuca.data_handlers import load_yaml, save_yaml

APP_NAME = "yuca"


def update_data_after_run(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        AppData.instance()._update()

    return wrapper


class AppData:
    _instance: AppData | None = None

    def __init__(self):
        self.app_data_dir = Path(platformdirs.user_data_dir(APP_NAME)) / "data.yml"
        self.app_data_dir.parent.mkdir(parents=True, exist_ok=True)
        self.data = (
            load_yaml(str(self.app_data_dir)) if self.app_data_dir.exists() else {}
        )

        self.warehouses = self.data.get("warehouses", []) or []
        self.default_wh = self.data.get("default_wh", 0)

    def _update(self):
        self.data["warehouses"] = self.warehouses
        self.data["default_wh"] = self.default_wh
        save_yaml(self.data, self.app_data_dir)

    @classmethod
    def instance(cls) -> AppData:
        if cls._instance is None:
            cls._instance = AppData()
        return cls._instance

    @staticmethod
    def get_warehouses() -> list[str]:
        inst = AppData.instance()
        return inst.warehouses

    @staticmethod
    def has_warehouses() -> bool:
        inst = AppData.instance()
        return len(inst.warehouses) > 0

    @staticmethod
    def get_default_warehouse() -> str:
        assert AppData.has_warehouses()
        inst = AppData.instance()
        return inst.warehouses[inst.default_wh]

    @staticmethod
    @update_data_after_run
    def set_default_warehouse(warehouse: int | str | Path):
        assert AppData.has_warehouses()
        inst = AppData.instance()
        if isinstance(warehouse, (str, Path)):
            warehouse = inst.warehouses.index(str(warehouse))
        inst.default_wh = warehouse

    @staticmethod
    @update_data_after_run
    def add_warehouse(dir: str | Path):
        dir = str(dir)
        inst = AppData.instance()
        if dir not in inst.warehouses:
            inst.warehouses.append(dir)
