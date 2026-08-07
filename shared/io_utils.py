from pathlib import Path
import yaml
import json
from shared.paths import schema_mappings 
from shared.paths import architectureInfo
from shared.verify import validate_schema

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

                message = f"❗ YAML formatting error in {path}{location}: {problem}"
                if context:
                    message = f"{message} ({context})"
                message = (
                    f"{message}\n"
                    "Hint: check indentation, missing ':', and list item '-' markers near that location."
                )
                raise ValueError(message) from error
    except FileNotFoundError as error:
        raise ValueError(f"❓ YAML file not found: {path}") from error
    except PermissionError as error:
        raise ValueError(f"⛔ Permission denied reading YAML file: {path}") from error
    except OSError as error:
        raise ValueError(f"⛔ Unable to read YAML file {path}: {error}") from error

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
                    f"🛑 JSON formatting error in {path} at line {error.lineno}, column {error.colno}: "
                    f"{error.msg}"
                    f"\n🔧 Possible file corruption. Backup gem5 source files and restore the original {path} from a clean gem5 source tree."
                )
                raise ValueError(message) from error
    except FileNotFoundError as error:
        raise FileNotFoundError(f"❓ JSON file not found: {path}") from error
    except PermissionError as error:
        raise PermissionError(f"⛔ Permission denied reading JSON file: {path}") from error
    except OSError as error:
        raise OSError(f"⛔ Unable to read JSON file {path}: {error}") from error

    resolved = path.resolve()
    schema = schema_mappings.get(resolved)
    if schema is not None:
        schema_name = path.stem.replace("-", "_") + "_schema"
        try:
            validate_schema(data, schema, name=schema_name)
        except ValueError as error:
            raise RuntimeError(f"🔧 Schema validation failed for {path}: {error}") from error

    return data


def load_registries() -> list[dict]:
    registries = []
    for arch in architectureInfo:
        registry_path = architectureInfo[arch]["registry_path"]
        try:
            registry_data = load_json(registry_path)
        except FileNotFoundError:
            write_json(registry_path, {"version": 0, "architecture": arch, "instructions": []})
            registry_data = {"version": 0, "architecture": arch, "instructions": []}
            print(f"🔶 Created new registry file for {arch} at {registry_path}")
        except ValueError:
            # load_json already built a fully-formatted message (JSON syntax error
            # with line/col, or a non-dict root) -- just let it propagate as-is.
            raise
        except RuntimeError:
            # load_json already built a fully-formatted schema validation message.
            raise
        except (PermissionError, OSError) as error:
            raise OSError(f"⛔ Unable to read registry file {registry_path}: {error}") from error

        registries.append(registry_data)
    return registries

def write_json(path: Path | str, data: dict) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)  # ensure the directory exists
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except PermissionError as error:
        raise ValueError(f"⛔ Permission denied writing JSON file: {path}") from error
    except OSError as error:
        raise ValueError(f"⛔ Unable to write JSON file {path}: {error}") from error