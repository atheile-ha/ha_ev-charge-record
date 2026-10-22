"""Tests for the translation files."""

import json
import re
from pathlib import Path

COMPONENT = Path(__file__).parent.parent / "custom_components" / "ev_charging"
LANGUAGES = ("en", "de")
# Option keys Home Assistant accepts: lower case, digits, "-" and "_", not at either end.
OPTION_KEY = re.compile(r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$")


def _keys(value, prefix=""):
    """Return the set of leaf key paths of a nested mapping."""
    if not isinstance(value, dict):
        return {prefix}
    return {key for name, item in value.items() for key in _keys(item, f"{prefix}.{name}")}


def test_base_language_matches_strings():
    """translations/en.json carries the same texts as strings.json."""
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    assert english == strings


def test_every_language_covers_the_same_keys():
    """No language is missing a key and none carries an unknown one."""
    expected = _keys(json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8")))
    for language in LANGUAGES:
        path = COMPONENT / "translations" / f"{language}.json"
        assert _keys(json.loads(path.read_text(encoding="utf-8"))) == expected


def test_no_text_is_empty():
    """Every translated text has content."""
    for language in LANGUAGES:
        path = COMPONENT / "translations" / f"{language}.json"
        stack = [json.loads(path.read_text(encoding="utf-8"))]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                stack.extend(item.values())
            else:
                assert isinstance(item, str) and item.strip()


def test_no_text_contains_an_unresolved_key_reference():
    """No shipped text is a [%key:...%] reference.

    Home Assistant only resolves these references at build time for
    integrations bundled with Home Assistant Core. A custom integration
    ships strings.json and translations/*.json directly, so every text
    must already be the literal, final value.
    """
    paths = [COMPONENT / "strings.json"]
    paths += [COMPONENT / "translations" / f"{language}.json" for language in LANGUAGES]
    for path in paths:
        stack = [json.loads(path.read_text(encoding="utf-8"))]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                stack.extend(item.values())
            else:
                assert "[%key:" not in item, f"{path}: {item}"


def test_selector_option_keys_are_valid():
    """Every option key under selector follows the key pattern Home Assistant accepts."""
    for path in [COMPONENT / "strings.json"] + [
        COMPONENT / "translations" / f"{language}.json" for language in LANGUAGES
    ]:
        selectors = json.loads(path.read_text(encoding="utf-8")).get("selector", {})
        for name, selector in selectors.items():
            for key in selector.get("options", {}):
                assert OPTION_KEY.match(key), f"{path.name}: selector.{name}.options.{key}"
