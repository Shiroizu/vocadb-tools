import importlib.util
from collections import defaultdict, deque
from importlib.resources import files
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

from bs4 import BeautifulSoup
from vdbpy.config import WIKI_URL
from vdbpy.utils.logger import get_logger
from vdbpy.utils.network import fetch_text

from .mod_types import (
    AutofixableRuleModule,
    RuleModule,
    RuleModules,
    RuleTableRow,
    TaggedRuleModule,
)

if TYPE_CHECKING:
    from vdbpy.types.shared import EntryStatus

logger = get_logger()


def topo_sort_graph(graph: dict[int, list[int]], all_rules: set[int]) -> list[int]:
    adj: defaultdict[int, list[int]] = defaultdict(list)
    indegree: defaultdict[int, int] = defaultdict(int)

    nodes = set(all_rules)
    for deps in graph.values():
        nodes.update(deps)

    for node, deps in graph.items():
        for dep in deps:
            adj[dep].append(node)
            indegree[node] += 1

    queue = deque([n for n in nodes if indegree[n] == 0])
    topo_result: list[int] = []

    while queue:
        n = queue.popleft()
        topo_result.append(n)
        for nxt in adj[n]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(topo_result) != len(nodes):
        raise ValueError("Cycle detected in rule dependency graph")

    dependent_rules = set(graph.keys())
    independent_rules = [r for r in topo_result if r not in dependent_rules]
    dep_sorted_rules = [r for r in topo_result if r in dependent_rules]

    return independent_rules + dep_sorted_rules


def validate_rule_module(module: ModuleType, rulefile: Path) -> bool:
    if not isinstance(module, RuleModule):
        missing = [
            attr
            for attr in ("MSG", "FIELDS", "ENTRY_TYPES", "COMPLETE", "AUTOMATICALLY_FIXED",
                         "check_entry_version_for_rule", "test")
            if not hasattr(module, attr)
        ]
        logger.warning(f"Rule check module {rulefile} is missing: {missing}")
        return False

    if module.AUTOMATICALLY_FIXED in (True, "Partially") and not isinstance(
        module, AutofixableRuleModule,
    ):
        logger.warning(
            f"Rule check module {rulefile} with AUTOMATICALLY_FIXED="
            f"{module.AUTOMATICALLY_FIXED} requires 'autofix()'",
        )
        return False

    if hasattr(module, "TAG_ID") and not isinstance(module, TaggedRuleModule):
        logger.warning(
            f"Rule check module {rulefile} with TAG_ID={module.TAG_ID} "
            "requires 'find_relevant_entries()'",
        )
        return False

    return True


def get_all_dependencies(
    rule_id: int,
    dependency_graph: dict[int, list[int]],
    _visited: set[int] | None = None,
) -> set[int]:
    """Recursively collect all dependencies for a given rule."""
    visited = _visited if _visited is not None else set()
    if rule_id in visited:
        return visited
    visited.add(rule_id)
    for dep in dependency_graph.get(rule_id, []):
        get_all_dependencies(dep, dependency_graph, visited)
    return visited


def get_bundled_modules_dir() -> Path:
    return Path(str(files("rule_modules").joinpath("modules")))


def get_rule_modules_by_id(
    path: Path | None = None, selected_rule_id: int = 0,
) -> RuleModules:
    if path is None:
        path = get_bundled_modules_dir()
    logger.debug(f"Loading rule modules from '{path}'")
    rule_dependency_graph: dict[int, list[int]] = {}
    rule_modules: RuleModules = {}
    python_files = list(Path(path).glob("*.py"))
    if selected_rule_id:
        logger.info(f"Selected rule id is {selected_rule_id}")
    logger.debug(f"Found {len(python_files)} python files...")
    for rulefile in python_files:
        logger.debug(rulefile)
        # Rule files are named {rule_id}_{rule_name}.py with rule_id > 0.
        if not rulefile.stem[:1].isdigit() or rulefile.stem.startswith("0_"):
            logger.debug(f"Skipping non-rule file: {rulefile.name}")
            continue

        rule_id_str, rule_name = rulefile.stem.split("_", 1)
        rule_id = int(rule_id_str)
        spec = importlib.util.spec_from_file_location(rulefile.stem, rulefile)
        module = None
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        if not module:
            logger.warning(f"Could not import rule check module {rulefile}")
            continue

        valid_rule_module = validate_rule_module(module, rulefile)
        if not valid_rule_module:
            logger.debug("Invalid rule module, continuing...")
            continue

        if hasattr(module, "ASSUME_VALID_FOR_RULE_ID"):
            rule_dependency_graph[rule_id] = module.ASSUME_VALID_FOR_RULE_ID

        rule_modules[rule_id] = (rule_name, module)

    if selected_rule_id:
        all_rule_ids = get_all_dependencies(selected_rule_id, rule_dependency_graph)
        rules_to_remove = set(rule_dependency_graph.keys()) - all_rule_ids
        for rule_id in rules_to_remove:
            logger.debug(f"Skipping rule module {rule_id}")
            rule_dependency_graph.pop(rule_id)
    else:
        all_rule_ids = set(rule_modules.keys())

    for rule_id, deps in rule_dependency_graph.items():
        for dep in deps:
            assert dep in all_rule_ids, (
                f"Missing dependency {dep} for {rule_id}, {all_rule_ids=}"
            )

    logger.debug(f"{rule_dependency_graph=}")
    logger.debug(f"{all_rule_ids=}")

    order = topo_sort_graph(rule_dependency_graph, all_rule_ids)
    return {
        rule_id: rule_modules[rule_id] for rule_id in order if rule_id in rule_modules
    }


EXPECTED_RULE_TABLE_HEADER = [
    "ID",
    "Date",
    "Name",
    "Entry type",
    "Entry status",
    "Rule context",
    "Relevant tag",
    "MikuMod support",
    "Complete",
    "Automatically fixed",
    "Edit list",
]


def get_rule_table() -> dict[int, RuleTableRow]:
    rows_to_return: dict[int, RuleTableRow] = {}
    html = fetch_text(f"{WIKI_URL}/rules/table")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        raise ValueError("No <table> found in rules/table HTML")
    header = table.find("thead")
    if not header:
        raise ValueError("Rules table is missing <thead>")
    header_text = [e.get_text(strip=True) for e in header.find_all("th")]
    if header_text != EXPECTED_RULE_TABLE_HEADER:
        raise ValueError(
            f"Unexpected rules table header: {header_text}",
        )
    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("Rules table is missing <tbody>")
    rows = tbody.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) != len(EXPECTED_RULE_TABLE_HEADER):
            raise ValueError(
                f"Expected {len(EXPECTED_RULE_TABLE_HEADER)} cells, got {len(cells)}",
            )
        rule_id = int(cells[0].get_text(strip=True))
        rule_name = cells[2].get_text(strip=True).lower().replace(" ", "-")
        rule_entry_type: list[str] = cells[3].get_text(strip=True).split(", ")
        rule_entry_status = cast("EntryStatus", cells[4].get_text(strip=True))
        tag_id_value = cells[6].get_text(strip=True)
        rule_tag_id = int(tag_id_value) if tag_id_value.isnumeric() else 0
        rule_complete = cells[8].get_text(strip=True).lower() == "true"
        match cells[7].get_text(strip=True).lower():
            case "true":
                rule_mikumodded = True
            case "false":
                rule_mikumodded = False
            case _:
                rule_mikumodded = "Planned"
        match cells[9].get_text(strip=True).lower():
            case "true":
                rule_autofixed = True
            case "false":
                rule_autofixed = False
            case _:
                rule_autofixed = "Partially"
        rows_to_return[rule_id] = RuleTableRow(
            rule_name,
            rule_entry_type,
            rule_entry_status,
            rule_tag_id,
            rule_mikumodded,
            rule_complete,
            rule_autofixed,
        )
    return rows_to_return
