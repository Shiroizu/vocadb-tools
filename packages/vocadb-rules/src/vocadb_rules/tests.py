# ruff: noqa: T201, PLR0915, TRY002, FURB171

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, cast, get_args

from vdbpy.api.edits import get_cached_edits_by_entry_before_version_id
from vdbpy.api.entries import (
    get_cached_entry_version,
    get_entry_link,
)
from vdbpy.config import WEBSITE
from vdbpy.types.changed_fields import ChangedFields
from vdbpy.types.mappings import changed_fields_by_entry_type
from vdbpy.types.mappings import (
    renamed_version_fields_to_changed_fields_mapping_by_entry_type as field_mapping,
)
from vdbpy.types.shared import EntryStatus, EntryType, VersionedEntryType
from vdbpy.utils.data import add_s
from vdbpy.utils.files import get_lines
from vdbpy.utils.logger import get_logger

from rule_modules.mod_types import (
    CheckResult,
    CorrectTestResults,
    RuleModuleResult,
    RuleModules,
    RuleTableRow,
)
from rule_modules.rules import (
    get_bundled_modules_dir,
    get_rule_modules_by_id,
    get_rule_table,
)

logger = get_logger()


def extract_function_lines(lines: list[str]) -> dict[str, list[str]]:
    functions: dict[str, list[str]] = {}
    current_func = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def "):
            if current_func:
                functions[current_func] = current_lines

            current_func = stripped.split(" ")[1].split("(")[0]
            current_lines = []
        elif current_func:
            current_lines.append(line)

    if current_func:
        functions[current_func] = current_lines

    return functions


def snake_case_to_pascal_case(word: str) -> str:
    # hello_world --> HelloWorld
    words = word.split("_")
    return "".join([word.capitalize() for word in words])


def get_rule_entry_status(
    rule_id: int,
    rule_name: str,
    rule_modules_dir: Path,
) -> EntryStatus:
    code = get_lines(rule_modules_dir / f"{rule_id}_{rule_name}.py")
    for line in code:
        if 'if version_data.status == "Draft":' in line:
            return "Finished"
        if 'if version_data.status != "Approved":' in line:
            return "Approved"
    return "Draft"


def flatten_literals(tp: Any) -> set[str]:
    values: set[Any] = set()
    for arg in get_args(tp):
        # Nested Literal
        if getattr(arg, "__origin__", None) is Literal:
            values.update(get_args(arg))
        else:
            values.add(arg)
    return values


def run_edit_and_entry_tests(
    check_function: Callable[..., tuple[int, str, int, int]] | None,
    rule_modules_by_rule_id: RuleModules,
    rule_module_dir: Path,
) -> None:
    """Run edit-check tests, and entry-check tests if `check_function` is given."""
    # Skip 'Wrong entry type'
    missing_edit_check_tests: dict[int, list[RuleModuleResult]] = {}

    # Require 'Wrong entry type' if rule_module.ENTRY_TYPES
    missing_entry_check_tests: dict[int, list[CheckResult]] = {}

    total_rules = len(rule_modules_by_rule_id)
    total_edit_versions = sum(
        sum(len(v) for v in mod.test()[0].values())
        for _, mod in rule_modules_by_rule_id.values()
    )
    logger.info(
        f"Will run {total_edit_versions} edit-check version test(s)"
        f" across {total_rules} rule(s)."
        f" First run is slow (network); subsequent runs hit the cache.",
    )

    for rule_index, (rule_id, (rule_name, rule_module)) in enumerate(
        rule_modules_by_rule_id.items(),
        start=1,
    ):
        logger.info(
            f"\n[{rule_index}/{total_rules}] === R{rule_id} {rule_name} ===",
        )
        # Verify matching rule entry status if rule deps
        # ASSUME_VALID_FOR_RULE_ID: list[int] = [24, 25]
        if hasattr(rule_module, "ASSUME_VALID_FOR_RULE_ID"):
            rule_entry_status = get_rule_entry_status(
                rule_id,
                rule_name,
                rule_module_dir,
            )
            for dep_rule_id in rule_module.ASSUME_VALID_FOR_RULE_ID:
                dep_rule_name, _ = rule_modules_by_rule_id[dep_rule_id]
                dep_rule_entry_status = get_rule_entry_status(
                    dep_rule_id,
                    dep_rule_name,
                    rule_module_dir,
                )
                if rule_entry_status == "Approved":
                    continue
                if rule_entry_status == "Finished" and dep_rule_entry_status == "Draft":
                    continue
                assert rule_entry_status == dep_rule_entry_status, (
                    f"Rule {rule_id}-{rule_name} dep {dep_rule_id}-{dep_rule_name}"
                    f" has a lower rule entry status:"
                    f" {rule_entry_status} < {dep_rule_entry_status}"
                )

        tests: CorrectTestResults = rule_module.test()
        edit_check_tests, entry_check_tests = tests

        if rule_id in [94]:
            continue  # TODO fix
        assert edit_check_tests, f"No edit check tests for {rule_id}-{rule_name}"

        possible_rule_module_return_values: set[RuleModuleResult] = set()
        code = get_lines(rule_module_dir / f"{rule_id}_{rule_name}.py")
        functions = extract_function_lines(code)
        rule_check_function_lines = functions["check_entry_version_for_rule"]

        # Check for matching changed fields
        entry_type: EntryType | Literal["Shared"]
        if len(rule_module.ENTRY_TYPES) == 1:
            entry_type = rule_module.ENTRY_TYPES[0]
        else:
            entry_type = "Shared"
        logger.debug(f"{rule_module.ENTRY_TYPES=} -> Using entry type {entry_type}")
        accessed_fields: set[str] = set()
        for line in rule_check_function_lines:
            words = line.strip().split()
            for word in words:
                r_stripped = word.lstrip("({")
                if r_stripped.startswith("version_data."):
                    field = r_stripped.split(".")[1].rstrip(",:)}")
                    logger.debug(f"Found field 'version_data.{field}'")
                    if field not in ["entry_id", "version_id"]:
                        accessed_fields.add(field)
        as_changed_fields: set[str] = set()
        for field in accessed_fields:
            logger.debug(f"Processing field {field}")
            if field in cast("Any", field_mapping)[entry_type]:
                mapped_field = cast("Any", field_mapping)[entry_type][field]
                logger.debug(f"Renamed field: {mapped_field}")
            elif field == "pvs":
                mapped_field = "PVs"
            elif field in cast("Any", field_mapping)["Shared"]:
                mapped_field = cast("Any", field_mapping)["Shared"][field]
                logger.debug(f"Renamed shared field: {mapped_field}")
            else:
                mapped_field = snake_case_to_pascal_case(field)
                logger.debug(f"Converted field: {mapped_field}")
                if mapped_field != "Status":
                    assert mapped_field in flatten_literals(ChangedFields), (
                        f"Unknown field '{mapped_field}' for {rule_id}_{rule_name}"
                    )
            as_changed_fields.add(mapped_field)

        # Check for valid changed fields (correct entry type)
        if len(rule_module.ENTRY_TYPES) > 0:
            for field in rule_module.FIELDS:
                if field == "Status":
                    continue
                own: set[ChangedFields] = set()
                for entry_type in rule_module.ENTRY_TYPES:
                    own.update(get_args(changed_fields_by_entry_type[entry_type]))
                shared = get_args(changed_fields_by_entry_type["Shared"])
                assert field in own or field in shared, (
                    f"Unknown field '{field}' for {rule_module.ENTRY_TYPES}"
                    f" (R{rule_id}), \n{own=}, \n{shared=}"
                )

        assert set(rule_module.FIELDS) == as_changed_fields, (
            f"Rule module (R{rule_id}) fields do not match code fields: "
            f"{rule_module.FIELDS} != {as_changed_fields}"
        )
        logger.info(
            f"R{rule_id}: rule module fields {set(rule_module.FIELDS)} match"
            f" with the code {accessed_fields}",
        )

        # Check for missing tests (1 rule violation test case for each entry type)
        required_test_entry_types = (
            get_args(VersionedEntryType)
            if not rule_module.ENTRY_TYPES
            else rule_module.ENTRY_TYPES
        )
        rule_violation_entry_types = {t[0] for t in edit_check_tests["Rule violation"]}

        missing_edit_check_test_whitelist = [8]
        for entry_type in required_test_entry_types:
            if rule_id in missing_edit_check_test_whitelist:
                continue
            assert entry_type in rule_violation_entry_types, (
                f"Missing rule violation edit check test for {entry_type} (R{rule_id})"
            )

        # Check for missing tests (based on possible rule module outputs)
        for line in rule_check_function_lines:
            stripped = line.strip()
            if stripped.startswith("return"):
                assert stripped.count('"') == 2, (
                    f"Keep 'return's on separate lines: {stripped}"
                )
                return_value: RuleModuleResult = cast(
                    "RuleModuleResult",
                    stripped.split('"')[1],
                )
                assert return_value in get_args(RuleModuleResult), return_value
                if return_value == "Wrong entry type":
                    continue
                possible_rule_module_return_values.add(return_value)

        for possible_return_value in possible_rule_module_return_values:
            if possible_return_value not in edit_check_tests:
                logger.warning(
                    f"R{rule_id} missing edit check test for {possible_return_value}",
                )
                missing_edit_check_tests.setdefault(rule_id, []).append(
                    possible_return_value,
                )
            if (
                check_function is not None
                and possible_return_value not in entry_check_tests
            ):
                logger.warning(
                    f"R{rule_id} missing entry check test for {possible_return_value}",
                )
                missing_entry_check_tests.setdefault(rule_id, []).append(
                    possible_return_value,
                )

        if (
            check_function is not None
            and rule_module.ENTRY_TYPES
            and "Wrong entry type" not in entry_check_tests
        ):
            missing_entry_check_tests.setdefault(rule_id, []).append("Wrong entry type")

        # Check for derived field tests
        changed_fields: ChangedFields = rule_module.FIELDS
        derived_fields: dict[EntryType, tuple[list[ChangedFields], str]] = {
            "Song": (["Lyrics"], "original_version_id"),
            "ReleaseEvent": (["OriginalName", "Names", "Category"], "series"),
            "Artist": (["BaseVoicebank"], "vb_base_id"),
        }

        derived_test_whitelist: list[int] = [97]
        for entry_type, (derived_field_list, version_key) in derived_fields.items():
            if entry_type in rule_module.ENTRY_TYPES:
                for derived_field in derived_field_list:
                    if derived_field in changed_fields:
                        derived_field_test_found = False
                        non_derived_test_found = False
                        rule_violation_version_tests = edit_check_tests[
                            "Rule violation"
                        ]
                        for test in rule_violation_version_tests:
                            logger.info(
                                f"Number of 'Rule Violation' version tests:"
                                f" {len(rule_violation_version_tests)}",
                            )
                            if test[0] == entry_type:
                                version_id = test[2]
                                version_data = get_cached_entry_version(
                                    entry_type,
                                    version_id,
                                )
                                assert version_data
                                derived = version_data.__dict__[version_key]
                                if derived:
                                    derived_field_test_found = True
                                    logger.info(
                                        f"Found derived field tests v{version_id}:"
                                        f" {entry_type}, {derived_field}({version_key})",
                                    )
                                non_derived_test_found = True
                                logger.info(
                                    f"Found non-derived field tests for v{version_id}:"
                                    f" {entry_type}, {derived_field}({version_key})",
                                )
                        if rule_id in derived_test_whitelist:
                            continue

                        assert derived_field_test_found, (
                            f"Missing derived field EDIT test for {entry_type}."
                            f"{derived_field}({version_key}) (R{rule_id})"
                        )
                        assert non_derived_test_found, (
                            f"Missing non-derived field EDIT test for {entry_type}."
                            f"{derived_field}({version_key}) (R{rule_id})"
                        )

        # Run edit check tests
        edit_test_count = sum(len(v) for v in edit_check_tests.values())
        logger.info(
            f"  Running {edit_test_count} edit-check version test(s)"
            f" for R{rule_id} {rule_name}...",
        )
        edit_test_index = 0
        for correct_check_result, version_tuples in edit_check_tests.items():
            for entry_type, entry_id, version_id in version_tuples:
                edit_test_index += 1
                # verify correct version id
                logger.info(
                    f"    [{edit_test_index}/{edit_test_count}]"
                    f" v{version_id} {get_entry_link(entry_type, entry_id)}"
                    f" -> expect '{correct_check_result}'",
                )
                version_ids: list[int] = [
                    edit.version_id
                    for edit in get_cached_edits_by_entry_before_version_id(
                        entry_type,
                        entry_id,
                        version_id,
                        include_deleted=True,
                    )
                ]
                assert version_id in version_ids

                entry_version_data = get_cached_entry_version(entry_type, version_id)
                test_check_result: RuleModuleResult = (
                    rule_module.check_entry_version_for_rule(entry_version_data)
                )
                if test_check_result != correct_check_result:
                    version_url = (
                        f"{WEBSITE}/api/{add_s(str(entry_type).lower())}"
                        f"/versions/{version_id}"
                    )
                    logger.warning(
                        f"Test failed for for {rule_id}_{rule_name}"
                        f" {version_url} :\n"
                        f"  Expected: {correct_check_result}\n"
                        f"  Actual:   {test_check_result}",
                    )
                    raise Exception(f"  Entry version data: {entry_version_data}")

        # Run entry check tests
        if check_function is None:
            continue
        if not entry_check_tests:
            logger.warning(f"Entry checks not found for {rule_id}_{rule_name}")
            continue

        logger.info(f"\nRunning ENTRY check tests for {rule_id}_{rule_name}")
        for correct_check_result, correct_check_data in entry_check_tests.items():
            assert correct_check_result != "Deleted"
            assert correct_check_result != "No data"
            assert correct_check_result != "Reverted"
            for (
                relevant_version_id,
                relevant_user_id,
                version_tuple,
            ) in correct_check_data:
                entry_type, entry_id, version_id = version_tuple
                assert entry_id
                entry_link = get_entry_link(entry_type, entry_id)
                logger.info(
                    f"Testing {entry_link} edits since"
                    f" v{version_id} (should be {correct_check_result})",
                )

                # verify correct version id
                version_ids = [
                    edit.version_id
                    for edit in get_cached_edits_by_entry_before_version_id(
                        entry_type,
                        entry_id,
                        version_id,
                        include_deleted=True,
                    )
                ]
                assert version_id in version_ids

                correct = (
                    version_id,
                    correct_check_result,
                    relevant_version_id,
                    relevant_user_id,
                )

                result: tuple[int, str, int, int] = check_function(
                    entry=(entry_type, entry_id),
                    version_id=version_id,
                    rule_id=rule_id,
                    check_all=False,
                    always_check_the_first_edit=False,
                    include_deleted=True,
                )
                if correct != result:
                    logger.warning(
                        f"Test failed for for {rule_id}_{rule_name}"
                        f" {entry_link} :\n"
                        f"  Expected: {correct}\n"
                        f"  Actual:   {result}",
                    )
                    raise Exception

                result2: tuple[int, str, int, int] = check_function(
                    entry=(entry_type, entry_id),
                    version_id=version_id,
                    rule_id=rule_id,
                    check_all=True,
                    always_check_the_first_edit=False,
                    include_deleted=True,
                )

                result3: tuple[int, str, int, int] = check_function(
                    entry=(entry_type, entry_id),
                    version_id=version_id,
                    rule_id=rule_id,
                    check_all=False,
                    always_check_the_first_edit=True,
                    include_deleted=True,
                )

                assert result[1] == result2[1] == result3[1], (
                    f"Something is very wrong! {result=}, {result2=}, {result3=}"
                )

    if missing_edit_check_tests:
        logger.warning("\nMissing edit check tests:")
        for rule_id, missing_test_cases in missing_edit_check_tests.items():
            logger.warning(f"- {rule_id}: {missing_test_cases}")
        if sys.stdin.isatty():
            _ = input("Press enter to continue")

    if missing_entry_check_tests:
        logger.warning("\nMissing entry check tests:")
        for rule_id, missing_test_cases in missing_entry_check_tests.items():
            logger.warning(f"- {rule_id}: {missing_test_cases}")
        if sys.stdin.isatty():
            _ = input("Press enter to continue")

    print()


def print_missing_rule_modules(
    existing_rule_ids: set[int],
    rule_table: dict[int, RuleTableRow],
) -> None:
    missing_rule_ids = set(rule_table.keys()) - existing_rule_ids
    logger.info("Missing rules:")
    for missing_rule_id in missing_rule_ids:
        missing_rule_fields = rule_table[missing_rule_id]
        if missing_rule_fields.rule_mikumodded == "Planned":
            logger.info(f"- {missing_rule_fields.rule_name}")


def verify_wiki_rule_fields(
    rule_modules_by_rule_id: RuleModules,
    rule_modules_dir: Path,
    rule_table: dict[int, RuleTableRow],
) -> None:
    for rule_id, (rule_name, rule_module) in rule_modules_by_rule_id.items():
        logger.debug(f"Verifying wiki rule fields for {rule_id}_{rule_name}")
        rule_wiki_fields = rule_table[rule_id]

        def compare_entry_types(
            code_fields: list[EntryType],
            wiki_fields: list[str],
        ) -> bool:
            # CODE: ["Song", "Artist", "Album", "Tag", "ReleaseEvent", "SongList",
            #        "Venue", "ReleaseEventSeries", "User"]
            # WIKI: "All"
            #    or ["Songs", "Albums", "Artists", "Events", "Tags", "Songlists"]

            if wiki_fields[0] == "All":
                return not code_fields

            if "Events" in wiki_fields:
                wiki_fields.remove("Events")
                wiki_fields.append("ReleaseEvent")

            wiki_fields = [field.rstrip("s") for field in wiki_fields]
            return set(code_fields) == set(wiki_fields)

        if not compare_entry_types(
            rule_module.ENTRY_TYPES,
            rule_wiki_fields.rule_entry_types_strings,
        ):
            logger.warning(
                f"Rule {rule_id}-{rule_name} has entry types {rule_module.ENTRY_TYPES}"
                f" in code but {rule_wiki_fields.rule_entry_types_strings} in wiki",
            )

        wiki_rule_name = rule_wiki_fields.rule_name
        wiki_rule_entry_status = rule_wiki_fields.rule_entry_status
        wiki_rule_autofixed = rule_wiki_fields.rule_autofixed
        wiki_rule_complete = rule_wiki_fields.rule_complete
        wiki_rule_mikumodded = rule_wiki_fields.rule_mikumodded

        rule_entry_status = get_rule_entry_status(rule_id, rule_name, rule_modules_dir)
        wiki_fields = {
            "name": (wiki_rule_name, rule_name),
            "entry status": (wiki_rule_entry_status, rule_entry_status),
            "autofixed": (wiki_rule_autofixed, rule_module.AUTOMATICALLY_FIXED),
            "complete": (wiki_rule_complete, rule_module.COMPLETE),
            "mikumodded": (wiki_rule_mikumodded, True),
        }

        for field_name, (wiki_field_value, code_field_value) in wiki_fields.items():
            if wiki_field_value != code_field_value:
                logger.warning(
                    f"\nModule: {rule_id}-{rule_name}, {field_name}: {code_field_value}"
                    f"\n=/=\nWiki: '{wiki_field_value}'\n",
                )

    # Check rules without modules

    if len(rule_modules_by_rule_id) < 10:
        # Assume running tests for individual rule
        return
    for rule_id, rule_wiki_fields in rule_table.items():
        if rule_id in rule_modules_by_rule_id:
            continue
        if rule_wiki_fields.rule_mikumodded == True:  # noqa: E712
            logger.warning(f"Rule {rule_id}-{rule_wiki_fields.rule_name} has no module")


def main() -> None:
    logger = get_logger("rule_modules_tests")

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--rule",
        type=int,
        default=0,
        help="Only test this rule id (and its declared dependencies).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging (per-version progress, cache hits, field analysis).",
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logger.setLevel(level)
    if args.debug:
        logger.debug("Debug logging enabled.")

    rule_modules_dir = get_bundled_modules_dir()
    rule_modules_by_rule_id = get_rule_modules_by_id(selected_rule_id=args.rule)

    if not rule_modules_by_rule_id:
        logger.error("No rule modules loaded, nothing to test.")
        raise SystemExit(1)

    rule_summary = ", ".join(
        f"R{rid} {name}" for rid, (name, _) in rule_modules_by_rule_id.items()
    )
    logger.info("=" * 72)
    logger.info(f"Loaded {len(rule_modules_by_rule_id)} rule module(s): {rule_summary}")
    logger.info("Plan:")
    logger.info(
        "  1. Edit-check tests (per-version: structural + check_entry_version_for_rule)",
    )
    logger.info("  Entry-check loop: SKIPPED (needs mikumod-style check_function)")
    logger.info("=" * 72)

    logger.info("\n[Step 1/2] Edit-check tests")
    run_edit_and_entry_tests(
        check_function=None,
        rule_modules_by_rule_id=rule_modules_by_rule_id,
        rule_module_dir=rule_modules_dir,
    )

    logger.info("\n[Step 2/2] Wiki cross-checks")
    logger.info("  Fetching rule table from wiki...")
    rule_table = get_rule_table()
    logger.info(f"  Got {len(rule_table)} rule(s) from wiki.")

    logger.info("  Planned rules without a module:")
    print_missing_rule_modules(set(rule_modules_by_rule_id.keys()), rule_table)

    logger.info("  Verifying wiki fields against module metadata...")
    verify_wiki_rule_fields(rule_modules_by_rule_id, rule_modules_dir, rule_table)

    logger.info("\n--- Passed all standalone tests! ---")


if __name__ == "__main__":
    main()
