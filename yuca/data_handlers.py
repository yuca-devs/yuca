import ruamel.yaml

yaml = ruamel.yaml.YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


def load_yaml(path: str):
    with open(path, "r") as yaml_fd:
        return yaml.load(yaml_fd)


def save_yaml(data: dict, path: str):
    with open(path, "w+") as yaml_fd:
        return yaml.dump(data, yaml_fd)


def load_template_config(path: str):
    return load_yaml(path)


def load_recipe(path: str):
    return load_yaml(path)


def load_user_data(path: str):
    return load_yaml(path)


def load_user_data_from_recipe(recipe: dict):
    path = recipe["user_data"]
    return load_yaml(path)
