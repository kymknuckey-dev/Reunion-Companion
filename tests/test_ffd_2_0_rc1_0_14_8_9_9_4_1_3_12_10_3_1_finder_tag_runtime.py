from pathlib import Path

from reunion_companion.companion import media_reconciliation as mr


def test_finder_tag_runtime_uses_macos_xattr_not_os_setxattr(monkeypatch, tmp_path):
    p = tmp_path / 'orphan.jpg'
    p.write_bytes(b'x')
    calls = []

    class CP:
        returncode = 0
        stdout = ''
        stderr = ''

    def fake_run(args, **kwargs):
        calls.append(list(args))
        return CP()

    monkeypatch.setattr(mr.subprocess, 'run', fake_run)
    mr._xattr_write(p, mr.FINDER_TAG_XATTR, b'abc')

    assert calls
    assert calls[0][:3] == ['/usr/bin/xattr', '-wx', mr.FINDER_TAG_XATTR]
