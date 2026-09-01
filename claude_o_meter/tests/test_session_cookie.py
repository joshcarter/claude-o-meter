"""Session-cookie handling: rotation persistence, seed invalidation, jitter.

Why this file exists: the poller authenticates with a browser `sessionKey`
cookie. If claude.ai rotates that cookie and we keep replaying the superseded
value, we look like a replayed/stolen cookie — and the standard server response
is to revoke the whole session family (i.e. log the user out everywhere). These
tests pin the rules that keep the chain correct across restarts.
"""

import json

import pytest

from claude_o_meter import poller


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    """Point the poller's state files at a tmp dir via DB_PATH, as in prod."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "samples.db"))
    return tmp_path


def test_no_saved_cookie_uses_env(state_dir, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-env")
    assert poller._load_session_cookie() == "sk-ant-sid01-env"


def test_rotated_cookie_survives_restart(state_dir, monkeypatch):
    """A rotation persisted in one run must be what the next run sends —
    otherwise every restart resurrects the value the server already replaced."""
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-env")
    poller._save_session_cookie("sk-ant-sid01-rotated")
    assert poller._load_session_cookie() == "sk-ant-sid01-rotated"


def test_new_env_key_discards_the_saved_chain(state_dir, monkeypatch):
    """User pastes a fresh sessionKey: the saved chain descends from the old
    seed and is dead, so the env value wins."""
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-old")
    poller._save_session_cookie("sk-ant-sid01-rotated")
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-new")
    assert poller._load_session_cookie() == "sk-ant-sid01-new"


def test_corrupt_cookie_file_falls_back_to_env(state_dir, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-env")
    poller._cookie_path().write_text("{not json")
    assert poller._load_session_cookie() == "sk-ant-sid01-env"


def test_forget_drops_the_chain(state_dir, monkeypatch):
    """What the 401/403 path does: a rejected cookie's whole chain is dead."""
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-env")
    poller._save_session_cookie("sk-ant-sid01-rotated")
    poller._forget_session_cookie()
    assert poller._load_session_cookie() == "sk-ant-sid01-env"
    poller._forget_session_cookie()  # idempotent — no file, no raise


def test_cookie_file_is_owner_only(state_dir, monkeypatch):
    """It holds a live credential; group/other must not be able to read it."""
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-env")
    poller._save_session_cookie("sk-ant-sid01-rotated")
    assert poller._cookie_path().stat().st_mode & 0o077 == 0


def test_saved_file_records_seed_and_current(state_dir, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_KEY", "sk-ant-sid01-env")
    poller._save_session_cookie("sk-ant-sid01-rotated")
    saved = json.loads(poller._cookie_path().read_text())
    assert saved == {"seed": "sk-ant-sid01-env", "current": "sk-ant-sid01-rotated"}


def test_org_cache_round_trip(state_dir):
    poller._write_private(poller._org_cache_path(), "0000-org-uuid\n")
    assert poller._read_org_cache() == "0000-org-uuid"


def test_org_cache_absent_is_none(state_dir):
    assert poller._read_org_cache() is None


def test_jitter_stays_within_band():
    """±POLL_JITTER around the nominal interval — never zero, never a burst."""
    samples = [poller._jittered(180) for _ in range(500)]
    assert all(180 * (1 - poller.POLL_JITTER) <= s <= 180 * (1 + poller.POLL_JITTER)
               for s in samples)
    assert len(set(samples)) > 1  # actually varying, not a constant
