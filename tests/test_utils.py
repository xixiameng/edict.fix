"""Tests for scripts/utils.py helpers."""
import pathlib
import sys

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import utils  # noqa: E402


def _make_repo_root(root: pathlib.Path) -> pathlib.Path:
    (root / 'scripts').mkdir(parents=True, exist_ok=True)
    (root / 'data').mkdir(parents=True, exist_ok=True)
    (root / 'scripts' / 'refresh_live_data.py').write_text('# stub\n', encoding='utf-8')
    return root


def test_resolve_repo_base_prefers_env(monkeypatch, tmp_path):
    repo = _make_repo_root(tmp_path / 'repoA')
    monkeypatch.setenv('EDICT_REPO_DIR', str(repo))
    got = utils.resolve_repo_base(tmp_path / 'x' / 'scripts' / 'kanban_update.py')
    assert got == repo


def test_resolve_repo_base_local_parent(tmp_path):
    repo = _make_repo_root(tmp_path / 'repoB')
    script = repo / 'scripts' / 'kanban_update.py'
    script.write_text('# stub\n', encoding='utf-8')
    got = utils.resolve_repo_base(script)
    assert got == repo
