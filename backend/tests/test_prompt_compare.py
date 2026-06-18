import json

from app.services.prompt_compare import (
    build_prompt_compare_report,
    render_prompt_compare_markdown,
    write_prompt_compare_report,
)


def test_build_prompt_compare_report_structure():
    baseline_report = {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "pass_rate": 0.5,
        "avg_latency_ms": 100.0,
        "badcase_count": 1,
        "results": [
            {
                "id": "case-1",
                "question": "What is the refund policy?",
                "pass": False,
                "score": 0.5,
                "failed_metrics": ["answer_keyword_recall"],
            },
            {
                "id": "case-2",
                "question": "What is billing support?",
                "pass": True,
                "score": 1.0,
                "failed_metrics": [],
            },
        ],
    }
    improved_report = {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "pass_rate": 1.0,
        "avg_latency_ms": 120.0,
        "badcase_count": 0,
        "results": [
            {
                "id": "case-1",
                "question": "What is the refund policy?",
                "pass": True,
                "score": 1.0,
                "failed_metrics": [],
            },
            {
                "id": "case-2",
                "question": "What is billing support?",
                "pass": True,
                "score": 1.0,
                "failed_metrics": [],
            },
        ],
    }

    report = build_prompt_compare_report(
        baseline_report=baseline_report,
        improved_report=improved_report,
        dataset_path="evals/datasets/real_rag_sample.jsonl",
    )

    assert report["provider"] == "deepseek"
    assert report["dataset"] == "evals/datasets/real_rag_sample.jsonl"
    assert report["baseline_pass_rate"] == 0.5
    assert report["improved_pass_rate"] == 1.0
    assert report["improved_cases"] == ["case-1"]
    assert report["regressed_cases"] == []
    assert report["changed_cases"][0]["id"] == "case-1"


def test_render_prompt_compare_markdown_contains_sections():
    compare_report = {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "dataset": "evals/datasets/real_rag_sample.jsonl",
        "generated_at": "2026-06-12T00:00:00+00:00",
        "baseline_pass_rate": 0.5,
        "improved_pass_rate": 1.0,
        "baseline_badcase_count": 1,
        "improved_badcase_count": 0,
        "baseline_avg_latency_ms": 100.0,
        "improved_avg_latency_ms": 120.0,
        "changed_cases": [
            {
                "id": "case-1",
                "question": "What is the refund policy?",
                "baseline_pass": False,
                "improved_pass": True,
                "baseline_failed_metrics": ["answer_keyword_recall"],
                "improved_failed_metrics": [],
            }
        ],
        "improved_cases": ["case-1"],
        "regressed_cases": [],
    }

    markdown = render_prompt_compare_markdown(compare_report)

    assert "# DeepSeek Prompt A/B Evaluation Report" in markdown
    assert "## Metric Comparison" in markdown
    assert "## Improved Cases" in markdown
    assert "answer_keyword_recall" in markdown


def test_write_prompt_compare_report_writes_json_and_markdown(tmp_path):
    baseline_report_path = tmp_path / "baseline.json"
    improved_report_path = tmp_path / "improved.json"
    compare_report_path = tmp_path / "compare.json"
    baseline_report_path.write_text(
        json.dumps(
            {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "pass_rate": 0.0,
                "avg_latency_ms": 100.0,
                "badcase_count": 1,
                "results": [
                    {
                        "id": "case-1",
                        "question": "q",
                        "pass": False,
                        "score": 0.0,
                        "failed_metrics": ["answer_keyword_recall"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    improved_report_path.write_text(
        json.dumps(
            {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "pass_rate": 1.0,
                "avg_latency_ms": 120.0,
                "badcase_count": 0,
                "results": [
                    {
                        "id": "case-1",
                        "question": "q",
                        "pass": True,
                        "score": 1.0,
                        "failed_metrics": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    write_prompt_compare_report(
        baseline_report_path=baseline_report_path,
        improved_report_path=improved_report_path,
        compare_report_path=compare_report_path,
        dataset_path="evals/datasets/real_rag_sample.jsonl",
    )

    assert compare_report_path.exists()
    assert compare_report_path.with_suffix(".md").exists()
