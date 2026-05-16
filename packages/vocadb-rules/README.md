VocaDB rule modules. 

Each rule encapsulates one wiki rule from <https://wiki.vocadb.net/rules>

## Usage

```python
from rule_modules import get_rule_modules_by_id

rule_modules = get_rule_modules_by_id()

from vdbpy.api.entries import get_cached_entry_version
version_data = get_cached_entry_version("Song", 1501)

for rule_id, (rule_name, module) in rule_modules.items():
  print(rule_id, rule_name, module.MSG)
  result = rule_modules[24][1].check_entry_version_for_rule(version_data)
  # -> "Valid" | "Not applicable" | "Rule violation" | "Wrong entry type" | ...
```

### Testing

```sh
uv run python -m rule_modules.tests              
uv run python -m rule_modules.tests --rule 8
```