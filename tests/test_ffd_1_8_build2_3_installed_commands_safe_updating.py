from pathlib import Path
import importlib.util
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

upd=load('companion_update',ROOT/'tools/companion_update.py')
inst=load('install_commands',ROOT/'tools/install_companion_commands.py')


def test_release_filter_excludes_wip_and_sorts_versions(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); subprocess.run(['git','init','-q'],cwd=repo,check=True)
    subprocess.run(['git','config','user.email','test@example.invalid'],cwd=repo,check=True)
    subprocess.run(['git','config','user.name','Test'],cwd=repo,check=True)
    (repo/'x').write_text('x'); subprocess.run(['git','add','.'],cwd=repo,check=True); subprocess.run(['git','commit','-qm','x'],cwd=repo,check=True)
    for tag in ('ffd-1.8-build-2.1.2','ffd-1.8-build-2.2','ffd-1.8-build-2.1-wip'):
        subprocess.run(['git','tag',tag],cwd=repo,check=True)
    tags=upd.accepted_tags(repo)
    assert tags[0]=='ffd-1.8-build-2.2'
    assert all('wip' not in t for t in tags)


def test_dirty_checkout_is_detected(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir(); subprocess.run(['git','init','-q'],cwd=repo,check=True)
    subprocess.run(['git','config','user.email','test@example.invalid'],cwd=repo,check=True)
    subprocess.run(['git','config','user.name','Test'],cwd=repo,check=True)
    (repo/'x').write_text('x'); subprocess.run(['git','add','.'],cwd=repo,check=True); subprocess.run(['git','commit','-qm','x'],cwd=repo,check=True)
    assert upd.worktree_clean(repo)
    (repo/'x').write_text('changed')
    assert not upd.worktree_clean(repo)


def test_command_installer_creates_launch_and_update_wrappers(tmp_path, monkeypatch):
    repo=tmp_path/'repo'; (repo/'.venv/bin').mkdir(parents=True); (repo/'tools').mkdir()
    (repo/'.venv/bin/python').write_text(''); (repo/'tools/companion_update.py').write_text('')
    bindir=tmp_path/'bin'
    c,u=inst.install(repo,bindir,update_profile=False)
    assert c.exists() and u.exists()
    assert '-m reunion_companion.companion.ui' in c.read_text()
    assert 'companion_update.py' in u.read_text()
    assert str(repo.resolve()) in u.read_text()


def test_bootstrap_knows_how_to_install_commands():
    text=(ROOT/'tools/bootstrap_portable_mac.py').read_text()
    assert '--install-commands' in text
    assert 'install_companion_commands' in text
