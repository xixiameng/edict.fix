#!/usr/bin/env python3
"""
三省六部 · 公共工具函数
避免 read_json / now_iso 等基础函数在多个脚本中重复定义
"""
import json, pathlib, datetime, os


def read_json(path, default=None):
    """安全读取 JSON 文件，失败返回 default"""
    try:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception:
        return default if default is not None else {}


def now_iso():
    """返回 UTC ISO 8601 时间字符串（末尾 Z）"""
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def today_str(fmt='%Y%m%d'):
    """返回今天日期字符串，默认 YYYYMMDD"""
    return datetime.date.today().strftime(fmt)


def safe_name(s: str) -> bool:
    """检查名称是否只含安全字符（字母、数字、下划线、连字符、中文）"""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$', s))


def validate_url(url: str, allowed_schemes=('https',), allowed_domains=None) -> bool:
    """校验 URL 合法性，防 SSRF"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if parsed.scheme not in allowed_schemes:
            return False
        if allowed_domains and parsed.hostname not in allowed_domains:
            return False
        if not parsed.hostname:
            return False
        # 禁止内网地址
        import ipaddress
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                return False
        except ValueError:
            pass  # hostname 不是 IP，放行
        return True
    except Exception:
        return False


def _looks_like_repo_root(base: pathlib.Path) -> bool:
    """Check whether a path looks like the edict project root."""
    if not isinstance(base, pathlib.Path):
        return False
    return (
        (base / 'scripts').is_dir()
        and (base / 'data').is_dir()
        and (base / 'scripts' / 'refresh_live_data.py').exists()
    )


def resolve_repo_base(current_file) -> pathlib.Path:
    """
    Resolve canonical edict repo root even when script is executed from
    ~/.openclaw/workspace-*/scripts copies.
    """
    # 1) explicit env
    for key in ('EDICT_REPO_DIR', 'OPENCLAW_REPO_DIR', 'REPO_DIR'):
        val = str(os.environ.get(key, '')).strip()
        if val:
            p = pathlib.Path(val).expanduser()
            if _looks_like_repo_root(p):
                return p

    # 2) installer pointer file
    pointer = pathlib.Path.home() / '.openclaw' / 'edict_repo_dir'
    if pointer.exists():
        try:
            p = pathlib.Path(pointer.read_text(encoding='utf-8').strip()).expanduser()
            if _looks_like_repo_root(p):
                return p
        except Exception:
            pass

    # 3) local parent of current script (works when running from repo/scripts)
    local = pathlib.Path(current_file).resolve().parent.parent
    if _looks_like_repo_root(local):
        return local

    # 4) walk up from cwd
    cwd = pathlib.Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        if _looks_like_repo_root(p):
            return p

    # 5) common home candidates
    home = pathlib.Path.home()
    for name in ('edict', 'edict.fix', 'openclaw-sansheng-liubu'):
        p = home / name
        if _looks_like_repo_root(p):
            return p

    # 6) fallback: keep previous behavior
    return local
