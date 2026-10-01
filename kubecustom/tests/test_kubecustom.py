"""
Unit and regression test for the kubecustom package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

from kubecustom.utils import convert_cpu_use, convert_memory_use


def test_kubecustom_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "kubecustom" in sys.modules


class TestConvertMemoryUse:
    """Regression tests for :func:`convert_memory_use`."""

    @pytest.mark.parametrize(
        "quantity, expected",
        [
            ("32Gi", 32 * 1.073741824),
            ("350G", 350.0),
            ("1234567Ki", 1234567 * 1.024e-6),
            ("100M", 0.1),
        ],
    )
    def test_integer_quantities(self, quantity, expected):
        assert convert_memory_use(quantity) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "quantity, expected",
        [
            ("1.5Gi", 1.5 * 1.073741824),
            ("0.5Gi", 0.5 * 1.073741824),
            (".5Gi", 0.5 * 1.073741824),
        ],
    )
    def test_fractional_quantities(self, quantity, expected):
        """Fractional quantities are legal in Kubernetes; these used to raise."""
        assert convert_memory_use(quantity) == pytest.approx(expected)

    def test_surrounding_whitespace_is_stripped(self):
        """Whitespace used to reach float() and raise."""
        assert convert_memory_use("  32Gi  ") == pytest.approx(
            convert_memory_use("32Gi")
        )

    @pytest.mark.parametrize("quantity", ["Gi", "", "1.2.3Gi", "abc"])
    def test_unparseable_quantities_raise(self, quantity):
        with pytest.raises(ValueError):
            convert_memory_use(quantity)

    def test_unsupported_unit_raises(self):
        with pytest.raises(ValueError, match="not one of the supported units"):
            convert_memory_use("12Xi")


class TestConvertCpuUse:
    """Regression tests for :func:`convert_cpu_use`."""

    @pytest.mark.parametrize(
        "quantity, expected",
        [("8", 8.0), ("500m", 0.5), ("250m", 0.25)],
    )
    def test_integer_quantities(self, quantity, expected):
        assert convert_cpu_use(quantity, issue_warnings=False) == pytest.approx(
            expected
        )

    @pytest.mark.parametrize("quantity, expected", [("0.5", 0.5), ("1.5", 1.5)])
    def test_fractional_quantities(self, quantity, expected):
        """Fractional CPU quantities are legal in Kubernetes; these used to raise."""
        assert convert_cpu_use(quantity, issue_warnings=False) == pytest.approx(
            expected
        )

    def test_surrounding_whitespace_is_stripped(self):
        assert convert_cpu_use("  8  ", issue_warnings=False) == pytest.approx(8.0)

    def test_unsupported_unit_raises(self):
        with pytest.raises(ValueError, match="not one of the supported units"):
            convert_cpu_use("8x", issue_warnings=False)


def test_get_data_resolves_credentials_from_environment(monkeypatch):
    from kubecustom.secret import MyData

    dummy_config = {
        "dummy-config": {
            "configuration_type": "qca",
            "username": "DUMMY_KUBECUSTOM_USER",
            "password": "DUMMY_KUBECUSTOM_PASSWORD",
        }
    }
    monkeypatch.setattr(MyData, "_get_configurations", lambda self: dummy_config)
    monkeypatch.setattr(MyData, "configuration", "dummy-config")
    monkeypatch.setenv("DUMMY_KUBECUSTOM_USER", "dummy-user")
    monkeypatch.setenv("DUMMY_KUBECUSTOM_PASSWORD", "dummy-password")

    obj = MyData.__new__(MyData)
    assert obj.get_data("username") == "dummy-user"
    assert obj.get_data("password") == "dummy-password"

    monkeypatch.delenv("DUMMY_KUBECUSTOM_USER")
    with pytest.raises(ValueError, match="not defined in your environment"):
        obj.get_data("username")


def test_credentials_must_be_environment_variable_names():
    from kubecustom.secret import _check_env_var_name

    _check_env_var_name("password", "NRP_PASSWORD")
    with pytest.raises(ValueError, match="name of an environment variable"):
        _check_env_var_name("password", "my pass!word")
