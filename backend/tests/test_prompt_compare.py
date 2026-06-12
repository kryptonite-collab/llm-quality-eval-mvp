from app.services.prompt_compare import build_prompt_compare_report


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
