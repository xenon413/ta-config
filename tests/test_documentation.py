import hashlib
import json
from pathlib import Path

import pytest


def test_readme_examples():
    root = Path(__file__).resolve().parents[1]
    namespace = {}
    for block in (root / "README.md").read_text(encoding="utf-8-sig").split("```python\n")[1:]:
        exec(block.split("```", 1)[0], namespace)


def test_fixture_integrity():
    data = Path(__file__).parent / "data"
    hashes = json.loads((data / "sha256.json").read_text())
    for relative, expected in hashes.items():
        content = (data / relative).read_bytes()
        if not relative.endswith(".zip"):
            content = content.replace(b"\r\n", b"\n")
        assert hashlib.sha256(content).hexdigest() == expected, relative


def test_public_exports():
    import ta_config
    import ta_config.core
    from ta_config.core.registry import REGISTRY

    for name in ta_config.__all__:
        assert getattr(ta_config, name) is getattr(ta_config.core, name)
    for spec in REGISTRY.values():
        assert getattr(ta_config, spec.implementation.__name__) is spec.implementation
        assert getattr(ta_config, spec.config_type.__name__) is spec.config_type


def test_logs_never_format_arguments(caplog):
    import logging

    from ta_config.core.helper import log_lifecycle

    logger = logging.getLogger("test.safe")

    class Secret:
        def __repr__(self):
            raise AssertionError("secret formatted")

    @log_lifecycle(logger)
    def operation(value):
        return 3

    with caplog.at_level(logging.DEBUG):
        assert operation(Secret()) == 3
    assert "operation" in caplog.text

    @log_lifecycle(logger)
    def fail(value):
        raise ValueError("failure")

    with pytest.raises(ValueError):
        fail(Secret())
