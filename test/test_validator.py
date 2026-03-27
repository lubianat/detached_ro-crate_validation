import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from basic_ro_crate_checker import validate_rocrate

TEST_DIR = Path(__file__).parent


@pytest.mark.parametrize("file", (TEST_DIR / "valid").glob("*.json"), ids=lambda f: f.name)
def test_valid_ro_crate(file):
    result = validate_rocrate(str(file))
    assert result.is_valid


@pytest.mark.parametrize("file", (TEST_DIR / "invalid").glob("*.json"), ids=lambda f: f.name)
def test_invalid_ro_crate(file):
    result = validate_rocrate(str(file))
    assert not result.is_valid
