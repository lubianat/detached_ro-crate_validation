# detached-crate-validator

Minimal Detached RO-Crate 1.2 Structure Validator.

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
