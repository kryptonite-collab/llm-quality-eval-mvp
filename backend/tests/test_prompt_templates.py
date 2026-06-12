from app.services.prompt_templates import (
    get_prompt_path,
    load_prompt_template,
    normalize_prompt_version,
)


def test_prompt_files_are_readable():
    baseline_prompt = load_prompt_template("baseline")
    improved_prompt = load_prompt_template("improved")

    assert "context" in baseline_prompt.lower()
    assert "do not invent" in improved_prompt.lower()
    assert get_prompt_path("baseline").name == "baseline_prompt.txt"
    assert get_prompt_path("improved").name == "improved_rag_prompt.txt"


def test_prompt_version_aliases():
    assert normalize_prompt_version(None) == "baseline"
    assert normalize_prompt_version("base") == "baseline"
    assert normalize_prompt_version("improved_rag") == "improved"
    assert normalize_prompt_version("rag") == "improved"
