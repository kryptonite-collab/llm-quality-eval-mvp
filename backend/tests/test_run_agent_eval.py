import json

from scripts.run_agent_eval import run_agent_eval


def test_run_agent_eval_report_structure(tmp_path) -> None:
    json_report = tmp_path / "agent_eval_report.json"
    markdown_report = tmp_path / "agent_eval_report.md"

    report = run_agent_eval(
        json_report=str(json_report),
        markdown_report=str(markdown_report),
    )

    assert report["provider"] == "mock"
    assert report["model"] == "mock-agent-v1"
    assert report["dataset"] == "evals/datasets/agent_eval_sample.jsonl"
    assert report["total_cases"] == 10
    assert report["pass_rate"] == 1.0
    assert report["badcase_count"] == 0
    assert report["results"]
    assert "generated_at" in report

    saved_report = json.loads(json_report.read_text(encoding="utf-8"))
    assert saved_report["tool_call_accuracy_avg"] == 1.0
    assert saved_report["source_hit_rate"] == 1.0
    assert markdown_report.exists()
