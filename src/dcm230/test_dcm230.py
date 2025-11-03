# ruff: noqa: S101,PLR2004, N802

"""Test file for driver."""

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
        _ = meter._unpack(registers, 0x0001)  # noqa: SLF001

    """Test 2: Should raise exception due to 16-bit register overflow"""
    registers = [0x7FFF]
    with pytest.raises(ValueError, match="Input overflow EEE for 16-bit register: "):
        _ = meter._unpack(registers, 0x0001)  # noqa: SLF001


def test_V() -> None:
    """Test Get v."""
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
