"""Smoke test: public surface matches :data:`benj_stocks_normalized.__all__`."""

import benj_stocks_normalized as m


def test_all_exports_are_defined_and_importable() -> None:
    for name in m.__all__:
        assert hasattr(m, name), f"missing export: {name}"
        getattr(m, name)
