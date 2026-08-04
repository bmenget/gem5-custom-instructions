from pathlib import Path
import yaml
import json

def load_yaml(path: Path | str) -> dict:
    path = Path(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as error:
                mark = getattr(error, "problem_mark", None)
                problem = getattr(error, "problem", None) or "Invalid YAML syntax."
                context = getattr(error, "context", None)
                location = ""
                if mark is not None:
                    location = f" at line {mark.line + 1}, column {mark.column + 1}"

                message = f"YAML formatting error in {path}{location}: {problem}"
                if context:
                    message = f"{message} ({context})"
                message = (
                    f"{message}\n"
                    "Hint: check indentation, missing ':', and list item '-' markers near that location."
                )
                raise ValueError(message) from error
    except FileNotFoundError as error:
        raise ValueError(f"YAML file not found: {path}") from error
    except PermissionError as error:
        raise ValueError(f"Permission denied reading YAML file: {path}") from error
    except OSError as error:
        raise ValueError(f"Unable to read YAML file {path}: {error}") from error

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root in {path} must be a mapping/object.")
    return data


def load_json(path: Path | str) -> dict:
    path = Path(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as error:
                message = (
                    f"JSON formatting error in {path} at line {error.lineno}, column {error.colno}: "
                    f"{error.msg}"
                )
                raise ValueError(message) from error
    except FileNotFoundError as error:
        raise ValueError(f"JSON file not found: {path}") from error
    except PermissionError as error:
        raise ValueError(f"Permission denied reading JSON file: {path}") from error
    except OSError as error:
        raise ValueError(f"Unable to read JSON file {path}: {error}") from error

    if not isinstance(data, dict):
        raise ValueError(f"JSON root in {path} must be a mapping/object.")
    return data