import ruamel.yaml

yaml = ruamel.yaml.YAML()

def load_yaml(path: str):
    with open(path, "r") as yaml_fd:
        return yaml.load(yaml_fd)

def load_template_config(path: str):
    return load_yaml(path)

def load_recipe(path: str):
    return load_yaml(path)

def load_user_data(path: str):
    return load_yaml(path)

def load_user_data_from_recipe(recipe: dict):
    path = recipe["user_data"]
    return load_yaml(path)