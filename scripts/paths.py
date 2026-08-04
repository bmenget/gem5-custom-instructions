from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
INSTRUCTIONS_PATH = ROOT_DIR / "instructions.yaml"
DATA_DIR = ROOT_DIR / "data"

TEMPLATE_DIR = DATA_DIR / "templates"
LOOKUPS_DIR = DATA_DIR / "lookups"
STATE_DIR = DATA_DIR / "state"