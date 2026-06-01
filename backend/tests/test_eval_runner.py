import json

from app.services.eval_runner import load_eval_dataset, run_eval_dataset


def test_load_eval_dataset(tmp_path):
    dataset_path = tmp_path / "sample.jsonl"
    dataset_path.write_text(
        '{"id":"q001","question":"test one","expected_keywords":["test one"],"expected_source":"mock_policy.md","category":"basic"}\n'
        '{"id":"q002","question":"test two","expected_keywords":["test two"],"expected_source":"mock_policy.md","category":"basic"}\n',
        encoding="utf-8",
    )

    samples = load_eval_dataset(dataset_path)

    assert len(samples) == 2
    assert samples[0]["id"] == "q001"
    assert samples[1]["question"] == "test two"


def test_run_eval_dataset_writes_report(tmp_path):
    dataset_path = tmp_path / "sample.jsonl"
    report_path = tmp_path / "latest_report.json"

    dataset_path.write_text(
        '{"id":"q001","question":"test rag mode","expected_keywords":["test rag mode"],"expected_source":"mock_policy.md","category":"rag_fact"}\n'
        '{"id":"q002","question":"test missing keyword","expected_keywords":["impossible_keyword"],"expected_source":"mock_policy.md","category":"badcase"}\n',
        encoding="utf-8",
    )

    report = run_eval_dataset(
        dataset_path=dataset_path,
        report_path=report_path,
        use_rag=True,
        top_k=3,
    )

    assert report["total"] == 2
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["pass_rate"] == 0.5
    assert report["source_hit_rate"] == 1.0
    assert report["badcase_count"] == 1
    assert report["badcase_type_distribution"] == {"keyword_miss": 1}
    assert len(report["top_failed_cases"]) == 1
    assert len(report["badcases"]) == 1

    badcase = report["badcases"][0]
    assert badcase["id"] == "q002"
    assert badcase["question_id"] == "q002"
    assert badcase["question"] == "test missing keyword"
    assert badcase["answer"] == "Mock answer for question: test missing keyword"
    assert badcase["expected_keywords"] == ["impossible_keyword"]
    assert badcase["missing_keywords"] == ["impossible_keyword"]
    assert badcase["expected_source"] == "mock_policy.md"
    assert badcase["retrieved_sources"] == ["mock_policy.md"]
    assert badcase["score"] == 0.0
    assert badcase["answer_keyword_recall"] == 0.0
    assert badcase["source_hit_at_k"] is True
    assert badcase["badcase_type"] == "keyword_miss"
    assert badcase["failed_metrics"] == ["answer_keyword_recall"]
    assert "missing keywords: impossible_keyword" in badcase["reason"]
    assert badcase["created_at"]

    assert report_path.exists()

    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_report["total"] == 2
    assert saved_report["failed"] == 1
    assert saved_report["source_hit_rate"] == 1.0
    assert saved_report["badcase_count"] == 1
    assert saved_report["badcase_type_distribution"] == {"keyword_miss": 1}
    assert saved_report["top_failed_cases"][0]["question_id"] == "q002"
    assert saved_report["badcases"][0]["question_id"] == "q002"


def test_run_eval_dataset_uses_config_file(tmp_path):
    dataset_path = tmp_path / "sample.jsonl"
    report_path = tmp_path / "latest_report.json"
    config_path = tmp_path / "config.yaml"

    dataset_path.write_text(
        '{"id":"q001","question":"test config","expected_keywords":["test config"],"expected_source":"mock_policy.md","category":"config"}\n',
        encoding="utf-8",
    )

    config_path.write_text(
        f"dataset_path: {dataset_path}\n"
        f"report_path: {report_path}\n"
        "use_rag: true\n"
        "top_k: 3\n"
        "min_keyword_score: 1.0\n",
        encoding="utf-8",
    )

    report = run_eval_dataset(config_path=config_path)

    assert report["total"] == 1
    assert report["passed"] == 1
    assert report["config"]["use_rag"] is True
    assert report["config"]["top_k"] == 3
    assert report_path.exists()


def test_run_eval_dataset_reports_multiple_badcase_types(tmp_path):
    dataset_path = tmp_path / "sample.jsonl"
    report_path = tmp_path / "latest_report.json"

    dataset_path.write_text(
        '{"id":"q001","question":"test pass","expected_keywords":["test pass"],"expected_source":"mock_policy.md","category":"facts_qa","expected_behavior":"answer","badcase_type":null}\n'
        '{"id":"q002","question":"test keyword miss","expected_keywords":["impossible_keyword"],"expected_source":"mock_policy.md","category":"keyword_miss","expected_behavior":"answer","badcase_type":"keyword_miss"}\n'
        '{"id":"q003","question":"test refusal","expected_keywords":["cannot assist"],"expected_source":null,"category":"refusal","expected_behavior":"refuse","badcase_type":"refusal_expected"}\n',
        encoding="utf-8",
    )

    report = run_eval_dataset(
        dataset_path=dataset_path,
        report_path=report_path,
        use_rag=True,
        top_k=3,
    )

    assert report["total"] == 3
    assert report["source_hit_rate"] == 1.0
    assert report["badcase_type_distribution"] == {
        "keyword_miss": 1,
        "refusal_expected": 1,
    }
    assert len(report["top_failed_cases"]) == 2
    assert report["top_failed_cases"][0]["failed_metrics"]
    assert all("failed_metrics" in badcase for badcase in report["badcases"])
    assert report_path.exists()
