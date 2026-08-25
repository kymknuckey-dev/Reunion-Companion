from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_cli import main

def test_status_command_prints_compact_state(tmp_path,capsys):
    db=connect(tmp_path/"x.db")
    db.close()
    main(["--db",str(tmp_path/"x.db"),"status"])
    out=capsys.readouterr().out
    assert "enabled=False" in out
    assert "queued=0" in out

def test_pause_command_is_available(tmp_path,capsys):
    db=connect(tmp_path/"x.db")
    db.close()
    main(["--db",str(tmp_path/"x.db"),"pause"])
    out=capsys.readouterr().out
    assert "'enabled': False" in out
