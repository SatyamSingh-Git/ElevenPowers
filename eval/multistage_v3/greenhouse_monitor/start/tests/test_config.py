import json

import pytest

from greenhouse.config.layout import load_layout
from greenhouse.config.settings import Settings, load_settings
from greenhouse.config.thresholds import load_thresholds
from greenhouse.core.errors import ConfigError


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_settings_default_without_a_file(tmp_path):
    assert load_settings(tmp_path / "settings.json") == Settings()


def test_settings_file_overrides_some_defaults(tmp_path):
    settings = load_settings(write(tmp_path / "settings.json", {"stale_minutes": 45, "dry_margin": 3}))
    assert settings.stale_minutes == 45
    assert settings.dry_margin == 3.0
    assert settings.max_offset == 5.0


def test_unknown_setting_is_refused(tmp_path):
    with pytest.raises(ConfigError, match="unknown setting: stale_after"):
        load_settings(write(tmp_path / "settings.json", {"stale_after": 10}))


def test_setting_must_be_a_number(tmp_path):
    with pytest.raises(ConfigError, match="setting max_offset must be a number"):
        load_settings(write(tmp_path / "settings.json", {"max_offset": "5"}))


def test_whole_number_settings_refuse_fractions(tmp_path):
    with pytest.raises(ConfigError, match="setting stale_minutes must be a whole number"):
        load_settings(write(tmp_path / "settings.json", {"stale_minutes": 7.5}))


def test_layout_loads_zones_in_file_order(data_dir):
    layout = load_layout(data_dir / "layout.json")
    assert layout.ids() == ["gh1", "gh2"]
    assert layout.zone("gh1").target_moisture == 40.0
    assert layout.zone("gh2").flow_lpm is None


def test_unknown_zone_is_named(data_dir):
    with pytest.raises(ConfigError, match="unknown zone: gh9"):
        load_layout(data_dir / "layout.json").zone("gh9")


def test_layout_zone_needs_a_valve(tmp_path):
    path = write(tmp_path / "layout.json", {"zones": [{"id": "gh1", "name": "North", "crop": "tomato"}]})
    with pytest.raises(ConfigError, match="zone gh1 is missing valve"):
        load_layout(path)


def test_missing_layout_is_reported(tmp_path):
    with pytest.raises(ConfigError, match="layout not found: layout.json"):
        load_layout(tmp_path / "layout.json")


def test_zone_limits_override_site_limits_one_bound_at_a_time(tmp_path):
    thresholds = load_thresholds(write(tmp_path / "thresholds.json", {
        "*": {"temperature": {"low": 8, "high": 32}},
        "gh1": {"temperature": {"high": 28}},
    }))
    limits = thresholds.limits("gh1", "temperature")
    assert (limits.low, limits.high) == (8.0, 28.0)
    assert thresholds.limits("gh2", "temperature").high == 32.0
    assert thresholds.limits("gh2", "humidity").is_empty()


def test_limits_must_be_ordered(tmp_path):
    with pytest.raises(ConfigError, match="thresholds for gh1 humidity: low must be below high"):
        load_thresholds(write(tmp_path / "thresholds.json", {"gh1": {"humidity": {"low": 90, "high": 60}}}))
