from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROMPT_DIR = PROJECT_ROOT / "evals/prompts"

PROMPT_VERSION_FILES = {
    "baseline": "baseline_prompt.txt",
    "improved": "improved_rag_prompt.txt",
}


def normalize_prompt_version(prompt_version: str | None) -> str:
    version = (prompt_version or "baseline").lower().strip()

    if version in {"baseline", "base"}:
        return "baseline"

    if version in {"improved", "improved_rag", "rag"}:
        return "improved"

    raise ValueError("Unsupported prompt version. Expected one of: baseline, improved.")


def get_prompt_path(prompt_version: str | None) -> Path:
    normalized_version = normalize_prompt_version(prompt_version)
    return PROMPT_DIR / PROMPT_VERSION_FILES[normalized_version]


def load_prompt_template(prompt_version: str | None) -> str:
    prompt_path = get_prompt_path(prompt_version)
    return prompt_path.read_text(encoding="utf-8").strip()
