"""Tests for scripts/sync_agent_config.py compatibility helpers."""
import pathlib
import sys
import types

# Ensure scripts/ is importable.
SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS))

# file_lock.py imports fcntl; provide a stub on platforms without it.
try:
    import fcntl  # noqa: F401
except ModuleNotFoundError:
    sys.modules['fcntl'] = types.SimpleNamespace(
        LOCK_SH=1,
        LOCK_EX=2,
        LOCK_UN=8,
        flock=lambda _fd, _op: None,
    )

import sync_agent_config as sac


def test_resolve_allow_agents_prefers_top_level():
    agent_cfg = {
        'allowAgents': ['menxia', 'shangshu'],
        'subagents': {'allowAgents': ['legacy-only']},
    }
    assert sac.resolve_allow_agents(agent_cfg) == ['menxia', 'shangshu']


def test_resolve_allow_agents_fallback_to_subagents():
    agent_cfg = {'subagents': {'allowAgents': ['menxia', 'shangshu']}}
    assert sac.resolve_allow_agents(agent_cfg) == ['menxia', 'shangshu']


def test_resolve_allow_agents_invalid_types():
    agent_cfg = {'allowAgents': 'menxia', 'subagents': {'allowAgents': 'shangshu'}}
    assert sac.resolve_allow_agents(agent_cfg) == []


def test_merged_known_models_includes_runtime_custom_models():
    cfg = {
        'agents': {
            'list': [
                {'id': 'taizi', 'model': 'cpa/my-custom-model'},
                {'id': 'zhongshu', 'model': {'primary': 'myprovider/alpha-v2'}},
            ]
        }
    }

    merged = sac.merged_known_models(cfg, default_model='openai/gpt-4o')
    by_id = {m['id']: m for m in merged}

    assert 'cpa/my-custom-model' in by_id
    assert by_id['cpa/my-custom-model']['provider'] == 'Custom'
    assert by_id['cpa/my-custom-model']['label'] == 'my-custom-model'

    assert 'myprovider/alpha-v2' in by_id
    assert by_id['myprovider/alpha-v2']['provider'] == 'Custom'
    assert by_id['myprovider/alpha-v2']['label'] == 'alpha-v2'


def test_merged_known_models_deduplicates_existing_known_model():
    cfg = {'agents': {'list': [{'id': 'taizi', 'model': 'openai/gpt-4o'}]}}
    merged = sac.merged_known_models(cfg, default_model='openai/gpt-4o')
    ids = [m['id'] for m in merged]
    assert ids.count('openai/gpt-4o') == 1

