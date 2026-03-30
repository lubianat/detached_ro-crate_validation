# detached-crate-validator

Minimal Detached RO-Crate 1.2 Structure Validator.

Scope:

* JUST the version 1.2 of the RO-Crate specification, and not later versions.
* JUST detached RO-Crates, not attached ones.

For a proper validation library see e.g. https://pypi.org/project/roc-validator/

SPEC says:

> A Detached RO-Crate Package is an RO-Crate, defined in an RO-Crate Metadata Document without a defined root directory,
  where the RO-Crate Metadata Document content is accessed independently (e.g. as part of a programmatic API).

  Unlike an Attached RO-Crate Package, a Detached RO-Crate Package is not processed in a file-system context and thus
  does not carry a data payload in the same sense, but may reference data deposited separately, or purely reference
  contextual entities.


## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
python -m detached_crate_validator path/to/ro-crate-metadata.json
```

### Python API

```python
from detached_crate_validator import validate_rocrate

result = validate_rocrate("path/to/ro-crate-metadata.json")
print(result.is_valid)
print(result.errors)
print(result.warnings)
```

## Scope

- Only validates RO-Crate specification version 1.2
- Only validates detached RO-Crates (not attached ones)

## License

MIT
