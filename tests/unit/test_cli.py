from apps.cli.main import main


def test_version_reports_demo_mode(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["--version"]) == 0
    assert "[DEMO]" in capsys.readouterr().out
