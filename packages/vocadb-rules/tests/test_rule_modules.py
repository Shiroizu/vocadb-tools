# ruff: noqa: S101
"""Pytest wrapper for `vocadb_rules.tests`.

Entry/edit tests through `uv run pytest -m rules`.
"""

import pytest

from vocadb_rules.rules import get_bundled_modules_dir, get_rule_modules_by_id
from vocadb_rules.tests import (
    SKIPPED_RULE_IDS,
    check_rule_derived_field_tests,
    check_rule_module_structure,
    run_rule_edit_check_tests,
)

RULE_MODULES = get_rule_modules_by_id()
MODULES_DIR = get_bundled_modules_dir()

RULE_IDS = [
    pytest.param(
        rule_id,
        id=f"R{rule_id}-{name}",
        marks=pytest.mark.skipif(
            rule_id in SKIPPED_RULE_IDS,
            reason="Known-broken rule module (TODO fix)",
        ),
    )
    for rule_id, (name, _) in sorted(RULE_MODULES.items())
]


def test_rule_modules_are_discoverable() -> None:
    assert RULE_MODULES, "No rule modules loaded"


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_module_structure(rule_id: int) -> None:
    rule_name, rule_module = RULE_MODULES[rule_id]
    check_rule_module_structure(
        rule_id,
        rule_name,
        rule_module,
        MODULES_DIR,
        RULE_MODULES,
    )


@pytest.mark.rules
@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_module_derived_field_tests(rule_id: int) -> None:
    _rule_name, rule_module = RULE_MODULES[rule_id]
    check_rule_derived_field_tests(rule_id, rule_module)


@pytest.mark.rules
@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_module_edit_checks(rule_id: int) -> None:
    rule_name, rule_module = RULE_MODULES[rule_id]
    run_rule_edit_check_tests(rule_id, rule_name, rule_module)
