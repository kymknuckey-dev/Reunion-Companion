from pathlib import Path

from reunion_companion.discovery.report import default_report_path


def test_report_path_strips_reunion_package_extension() -> None:
    path = default_report_path(
        "/tmp/Mervyn Knuckey 14.familyfile14",
        "object_classification",
        root="/tmp/reports/discovery",
    )
    assert "Mervyn_Knuckey_14.familyfile14" not in str(path)
    assert "Mervyn_Knuckey_14" in str(path)
    assert path.name == "object_classification.md"
    assert path.parent.parent.name == "Mervyn_Knuckey_14"
