from pathlib import Path
from reunion_companion.companion.shell import CompanionShell

def test_publication_capabilities_dispatch_exists(tmp_path):
    sh = CompanionShell(tmp_path/"test.sqlite3")
    result = sh.command("publication-capabilities")
    assert "Professional Publishing Capabilities" in result
    assert "PDF document preview renderer:" in result
    assert "Direct book PDF export:" in result
