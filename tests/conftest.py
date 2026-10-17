from collections.abc import Generator
from pathlib import Path
import shutil
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:
    """Provide an isolated temporary directory inside the test workspace."""
    test_root = Path(__file__).parent / ".pytest-tmp"
    test_dir = test_root / uuid4().hex
    test_dir.mkdir(parents=True)

    yield test_dir

    for child in test_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    test_dir.rmdir()
