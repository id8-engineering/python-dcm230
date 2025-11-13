# ruff: noqa: S101, PLR2004, SLF001

"""Test file for driver."""

from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest

from dcm230 import Dcm230


def test_unpack() -> None:
    """Test unpack."""
    client = MagicMock()
    meter = Dcm230(1, client)

    """Test 1: Should raise exception due to more registers in use than allowed."""
    registers = [0x1860, 0x0023, 0x4244]
    with pytest.raises(ValueError, match="Unexpected register count:"):
        _ = meter._unpack(registers, 0x0001)


def test_read_register() -> None:
    """Test read_register."""
    client = MagicMock()
    meter = Dcm230(1, client)

    """Test 1: Should raise exception due to incorrect register type"""
    address = 1
    count = 2
    reg_type = 0x05
    with pytest.raises(ValueError, match="Unsupported reg_type:"):
        _ = meter._read_registers(address, count, reg_type)

    """Test 2: Should NOT raise when using correct register type"""
    reg_type = 0x03
    client.read_input_registers.return_value.isError.return_value = False
    client.read_input_registers.return_value.registers = [100, 200]

    with nullcontext():
        _ = meter._read_registers(address, count, reg_type)


def test_range_validation() -> None:
    """Test range validation."""
    client = MagicMock()
    meter = Dcm230(1, client)

    """Test 1: Should not pass due to out of range."""
    for name, spec in Dcm230._register_specs.items():  # type: ignore[attr-defined]
        if not spec.range:
            continue

        client.write_registers.return_value.isError.return_value = False
        with nullcontext():
            _ = setattr(meter, name, spec.min)

        invalid_value = spec.max + 1
        with pytest.raises(ValueError, match="Invalid value for"):
            setattr(meter, name, invalid_value)

        invalid_value = spec.min - 1
        with pytest.raises(ValueError, match="Invalid value for"):
            setattr(meter, name, invalid_value)


def read_input_registers() -> None:
    """Test all input registers."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    meter = Dcm230(1, client)

    mock_result.registers = [0x3F80, 0x0000]
    client.read_input_registers.return_value = mock_result

    """Test 1: Should pass."""
    for name, spec in Dcm230._register_specs.items():  # type: ignore[attr-defined]
        if spec.reg_type != meter.INPUT_REGISTER:
            continue

        value = getattr(meter, name)
        assert value == 1


def read_holding_registers() -> None:
    """Test all holding registers."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    meter = Dcm230(1, client)

    mock_result.registers = [0x3F80, 0x0000]
    client.read_holding_registers.return_value = mock_result

    """Test 1: Should pass."""
    for name, spec in Dcm230._register_specs.items():  # type: ignore[attr-defined]
        if spec.reg_type != meter.HOLDING_REGISTER:
            continue

        value = getattr(meter, name)
        assert value == 1


def test_set_all_register() -> None:
    """Test set all registers."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    client.write_registers.return_value = mock_result

    meter = Dcm230(1, client)

    for name, spec in Dcm230._register_specs.items():  # type: ignore[attr-defined]
        if not spec.writable:
            continue

        value = 1
        setattr(meter, name, value)
        client.write_registers.assert_called_once_with(address=spec.address, values=[1], device_id=1)
        client.write_registers.reset_mock()


def test_backlit_time() -> None:
    """Test get and set backlit time."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    meter = Dcm230(1, client)

    """Test 1: should pass"""
    mock_result.registers = [0x4270, 0x0000]
    client.read_holding_registers.return_value = mock_result
    value = meter.backlit_time
    assert value == 60

    """Test 2: Should raise exception due to invalid backlit option."""
    with pytest.raises(ValueError, match="Invalid backlit option:"):
        meter.backlit_time = 100

    """Test 3: should pass when set."""
    client.write_registers.return_value = mock_result
    meter.backlit_time = 60
    client.write_registers.assert_called_once_with(address=meter.DCM230_REGISTER_BACKLIT_TIME, values=[60], device_id=1)


def test_reset_functions() -> None:
    """Test all reset functions."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    client.write_registers.return_value = mock_result

    meter = Dcm230(1, client)

    """Test 1: reset_max_dmd."""
    meter.reset_max_dmd()
    client.write_registers.assert_called_once_with(
        address=meter.DCM230_REGISTER_RESET_MAX_DMD_AND_PARTIAL_ENERGY, values=[meter.RESET_MAX_DMD], device_id=1
    )

    client.write_registers.reset_mock()

    """Test 2: reset_partial_energy."""
    meter.reset_partial_energy()
    client.write_registers.assert_called_once_with(
        address=meter.DCM230_REGISTER_RESET_MAX_DMD_AND_PARTIAL_ENERGY, values=[meter.RESET_PARTIAL_ENERGY], device_id=1
    )
