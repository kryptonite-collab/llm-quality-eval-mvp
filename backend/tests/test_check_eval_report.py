from scripts.check_eval_report import check_eval_report, main


def test_check_eval_report_passes_when_thresholds_are_met():
    passed, messages = check_eval_report(
        report={"pass_rate": 0.8, "badcase_count": 2},
        min_pass_rate=0.7,
        max_badcase_count=3,
    )

    assert passed is True
    assert messages == []


def test_check_eval_report_fails_when_pass_rate_is_too_low():
    passed, messages = check_eval_report(
        report={"pass_rate": 0.6, "badcase_count": 2},
        min_pass_rate=0.7,
        max_badcase_count=3,
    )

    assert passed is False
    assert "pass_rate 0.6 is below threshold 0.7" in messages


def test_check_eval_report_main_exit_codes(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text('{"pass_rate":0.8,"badcase_count":2}', encoding="utf-8")

    assert (
        main(
            [
                "--report-path",
                str(report_path),
                "--min-pass-rate",
                "0.7",
                "--max-badcase-count",
                "3",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "--report-path",
                str(report_path),
                "--min-pass-rate",
                "0.9",
            ]
        )
        == 1
    )
