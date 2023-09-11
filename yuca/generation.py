import logging
import re
import shutil
from pathlib import Path
from typing import Any, Iterable

import jinja2

from yuca.data_handlers import load_template_config

VALID_ESCAPE_FORMATS = ["latex"]
SETTINGS_VAR_REGEX = re.compile(r"([^\[\]]+)(\[(\d+)\]|)$")
route = list[str | int]


def fill_template_file(file: Path, content: dict = {}):
    environment = jinja2.Environment(
        comment_start_string="{=",
        comment_end_string="=}",
    )
    template = environment.from_string(file.read_text())
    rendered_content = template.render(content)
    file.write_text(rendered_content)


def escape_latex_special_chars(input_string):
    # Define a dictionary to map LaTeX special characters to their escaped counterparts
    latex_special_chars = {
        "\\": r"\\",
        "{": r"\{",
        "}": r"\}",
        "[": r"{[}",
        "]": r"{]}",
        "^": r"\^{}",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }

    # Iterate through the string and replace LaTeX special characters with their
    # escaped counterparts
    escaped_string = ""
    for char in input_string:
        if char in latex_special_chars:
            escaped_string += latex_special_chars[char]
        else:
            escaped_string += char

    return escaped_string


def escape_strings(data: dict | list, escape_format: str):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = escape_strings(value, escape_format)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = escape_strings(data[i], escape_format)
    elif isinstance(data, str):
        if escape_format == "latex":
            data = escape_latex_special_chars(data)
    return data


def _get_routes_and_vals(data: dict, curr_route=None) -> Iterable[tuple[route, Any]]:
    curr_route = [] if curr_route is None else curr_route
    for key, val in data.items():
        # Regex to get key name and index value.
        # It should give: match.groups() = [key_name, _, index]
        # examples:
        #   projects[0] -> ['projects', _, '0']
        #   institution -> ['institution', _, None]
        match = SETTINGS_VAR_REGEX.match(key)
        assert match is not None

        key_name, _, index = match.groups()
        curr_route += [key_name]

        if isinstance(val, dict):
            # Check if key represents a list in context. If so, add the index to
            # the route
            if index is not None:
                curr_route += [int(index)]

            yield from _get_routes_and_vals(data[key], curr_route=curr_route)
        else:
            yield curr_route, val

        # Remove last item and check if it was an integer (index). If so, remove
        # another item (the corresponding key)
        if isinstance(curr_route.pop(), int):
            curr_route.pop()


def _get_data_from_route(context: dict, route: list) -> tuple[dict, str]:
    data = context
    for route_item, next_route_item in zip(route[:-1], route[1:]):
        # If route element is an index, it has been handled in previous iteration
        if isinstance(route_item, int):
            continue

        # Traverse one step into the data structure following the given route
        data = data[route_item]

        # Check if next route item represents an index. If so, the current
        # route_item is a list in the data and a second traverse step is
        # performed
        if isinstance(next_route_item, int):
            assert isinstance(data, list)
            data = data[next_route_item]

        # Data must be a dict at the end of every iteration
        assert isinstance(data, dict)

    return data, route[-1]


def _process_filters(context, filters):
    for route, selected_indices in _get_routes_and_vals(filters):
        data, key = _get_data_from_route(context, route)
        data[key] = [data[key][i] for i in selected_indices]


def _process_overrides(context, overrides):
    for route, val in _get_routes_and_vals(overrides):
        data, key = _get_data_from_route(context, route)
        data[key] = val


def process_files(
    user_folder: Path,
    overridable_files: dict,
    output_folder: Path,
    user_files: dict,
):
    for key, user_file in user_files.items():
        template_file = overridable_files.get(key, None)
        if template_file is None:
            continue
        src_path = str(user_folder / user_file)
        dst_path = str(output_folder / template_file)
        shutil.copyfile(src_path, dst_path)


def preprocess_ctx_with_user_settings(context, user_config):
    _process_overrides(context, user_config.get("overrides", {}) or {})
    _process_filters(context, user_config.get("filters", {}) or {})


def generate(
    template_folder: Path, output_folder: Path, user_config: dict, user_data: dict
):
    shutil.copytree(template_folder, output_folder, dirs_exist_ok=True)

    config = load_template_config(str(template_folder / "config.yml"))
    context = user_data

    # Process files
    overridable_files = config.get("overridable_files", {}) or {}
    user_files = user_config.get("files", {}) or {}
    process_files(
        Path(user_config["static"]),
        overridable_files,
        output_folder,
        user_files,
    )

    # Process overrides and filters
    preprocess_ctx_with_user_settings(context, user_config)

    # Process scaping
    escape_format = config.get("scape_format")
    if escape_format is not None and escape_format in VALID_ESCAPE_FORMATS:
        context = escape_strings(context, escape_format)

    # Process settings
    settings: dict = config.get("default_settings", {}) or {}
    user_settings = user_config.get("settings", {}) or {}
    settings.update(user_settings)
    context["settings"] = settings

    # Handle when lang is not in config.yml
    context["intl"] = config["intl"].get(context["lang"])

    for temp_file in config["template_files"]:
        temp_file_path = output_folder / temp_file

        if not temp_file_path.exists():
            logging.error(f"Template {template_folder} does not contains {temp_file}")
            continue

        fill_template_file(temp_file_path, context)
