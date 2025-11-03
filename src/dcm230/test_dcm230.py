# ruff: noqa: S101,PLR2004, N802, SLF001

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


def test_V() -> None:
    """Test get v."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.isError.return_value = False
    meter = Dcm230(1, client)

    """Test 1: should pass"""
    mock_result.registers = [0x4366, 0x0000]
    client.read_input_registers.return_value = mock_result
    value = meter.V
    assert value == 230

    """Test 2: Should pass."""
    mock_result.registers = [0x4624, 0x1000]
    client.read_input_registers.return_value = mock_result
    value = meter.V
    assert value == 10500
