"""Tests for scripts/sync_agent_config.py compatibility helpers."""

import importlib.util
import json
import pathlib
import sys
import types
from pathlib import Path


def _ensure_fcntl_stub():
    # file_lock.py imports fcntl; provide a stub on platforms without it.
    try:
        import fcntl  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["fcntl"] = types.SimpleNamespace(
            LOCK_SH=1,
            LOCK_EX=2,
            LOCK_UN=8,
            flock=lambda _fd, _op: None,
        )


def _load_sync_agent_config():
    _ensure_fcntl_stub()
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "sync_agent_config.py"
    spec = importlib.util.spec_from_file_location("sync_agent_config", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_allow_agents_prefers_top_level():
    sac = _load_sync_agent_config()
    agent_cfg = {
        "allowAgents": ["menxia", "shangshu"],
        "subagents": {"allowAgents": ["legacy-only"]},
    }
    assert sac.resolve_allow_agents(agent_cfg) == ["menxia", "shangshu"]


def test_resolve_allow_agents_fallback_to_subagents():
    sac = _load_sync_agent_config()
    agent_cfg = {"subagents": {"allowAgents": ["menxia", "shangshu"]}}
    assert sac.resolve_allow_agents(agent_cfg) == ["menxia", "shangshu"]


def test_resolve_allow_agents_invalid_types():
    sac = _load_sync_agent_config()
    agent_cfg = {"allowAgents": "menxia", "subagents": {"allowAgents": "shangshu"}}
    assert sac.resolve_allow_agents(agent_cfg) == []


def test_merged_known_models_includes_runtime_custom_models():
    sac = _load_sync_agent_config()
    cfg = {
        "agents": {
            "list": [
                {"id": "taizi", "model": "cpa/my-custom-model"},
                {"id": "zhongshu", "model": {"primary": "myprovider/alpha-v2"}},
            ]
        }
    }
    merged = sac.merged_known_models(cfg, default_model="openai/gpt-4o")
    by_id = {m["id"]: m for m in merged}

    assert "cpa/my-custom-model" in by_id
    assert by_id["cpa/my-custom-model"]["provider"] == "Custom"
    assert by_id["cpa/my-custom-model"]["label"] == "my-custom-model"

    assert "myprovider/alpha-v2" in by_id
    assert by_id["myprovider/alpha-v2"]["provider"] == "Custom"
    assert by_id["myprovider/alpha-v2"]["label"] == "alpha-v2"


def test_merged_known_models_deduplicates_existing_known_model():
    sac = _load_sync_agent_config()
    cfg = {"agents": {"list": [{"id": "taizi", "model": "openai/gpt-4o"}]}}
    merged = sac.merged_known_models(cfg, default_model="openai/gpt-4o")
    ids = [m["id"] for m in merged]
    assert ids.count("openai/gpt-4o") == 1


def test_resolve_agent_dir_prefers_config_value():
    sac = _load_sync_agent_config()
    agent_cfg = {"agentDir": "/tmp/custom/agent-dir"}
    assert sac.resolve_agent_dir(agent_cfg, "taizi") == "/tmp/custom/agent-dir"


def test_resolve_agent_dir_fallback_to_default():
    sac = _load_sync_agent_config()
    expected = str(pathlib.Path.home() / ".openclaw/agents/taizi/agent")
    assert sac.resolve_agent_dir({}, "taizi") == expected


def test_sync_agent_config_accepts_allow_agents_key(tmp_path, monkeypatch):
    sync_agent_config = _load_sync_agent_config()

    cfg = {
        "agents": {
            "defaults": {"model": "openai/gpt-4o"},
            "list": [
                {
                    "id": "taizi",
                    "workspace": str(tmp_path / "ws-taizi"),
                    "allowAgents": ["zhongshu"],
                }
            ],
        }
    }

    cfg_path = tmp_path / "openclaw.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(sync_agent_config, "OPENCLAW_CFG", cfg_path)
    monkeypatch.setattr(sync_agent_config, "DATA", tmp_path / "data")

    sync_agent_config.main()

    out = json.loads((tmp_path / "data" / "agent_config.json").read_text(encoding="utf-8"))
    taizi = next(agent for agent in out["agents"] if agent["id"] == "taizi")
    assert taizi["allowAgents"] == ["zhongshu"]

