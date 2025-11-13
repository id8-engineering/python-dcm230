"""Driver class for Eastron DCM230 Modbus energy meters.

This module provides a generic, configurable driver for the Eastron Dcm230
series of energy meters, using pymodbus for serial communication.

The design uses dataclasses to define register specifications and a class
decorator to automatically generate @property accessors for all defined
registers. This minimizes boilerplate and ensures consistency across multiple
registers.
"""

import struct
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Final, TypeVar

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

T = TypeVar("T", bound=type)


@dataclass(frozen=True)
class RegisterSpec:
    """Specification for a Modbus register mapping.

    Defines the register address, scaling, precision, and read/write behavior.

    Attributes:
        address (int): Modbus register address.
        count (int): Number of consecutive registers to read.
        decimals (int): Number of decimal places to round the scaled value to.
        writable (bool): Whether this register can be written to.
        range (bool): Whether range validation should be performed.
        min (int): Minimum allowed value for range validation.
        max (int): Maximum allowed value for range validation.
    """

    address: int
    count: int
    reg_type: int
    decimals: int = 0
    range: bool = False
    min: int = 0
    max: int = 0x7FFFFFFF
    writable: bool = False
    return_type: type[int] | type[Decimal] = Decimal


def register_properties(cls: T) -> T:
    """Class decorator that auto-generates @property accessors for Modbus registers.

    For each entry in `cls._register_specs`, this decorator dynamically creates
    a corresponding @property getter, and optionally a setter if `writable=True`.

    The generated getter automatically calls `_read_register(register_name)`
    and the setter calls `_write_registers(address, value)` with range validation
    if enabled in the `RegisterSpec`.

    Args:
        cls: The target class to which properties will be added.

    Returns:
        The same class with dynamically added properties.
    """
    for name, spec in cls._register_specs.items():

        def getter(self: "Dcm230", _name: str = name, _spec: "RegisterSpec" = spec) -> Decimal | int:
            """Auto-generated register reader.

            Returns the current value of the register. If range validation is
            enabled, ensures that the returned value is within the expected range.

            Raises:
                ValueError: If the register value is outside its defined range.
            """
            _value = self._read_register(_name)
            if _spec.range and not (_spec.min <= _value <= _spec.max):
                msg = f"Invalid value for '{_name}': {_value}. Must be between {_spec.min} and {_spec.max}."
                raise ValueError(msg)
            return _value

        def setter(self: "Dcm230", value: int, _name: str = name, _spec: "RegisterSpec" = spec) -> None:
            """Auto-generated register writer.

            Writes a new value to the register and performs range validation
            if defined in the corresponding `RegisterSpec`.

            Raises:
                AttributeError: If the register is read-only.
                ValueError: If the written value is outside its defined range.
            """
            if not _spec.writable:
                msg = f"Register '{_name}' is read-only."
                raise AttributeError(msg)

            if _spec.range and not (_spec.min <= value <= _spec.max):
                msg = f"Invalid value for '{_name}': {value}. Must be between {_spec.min} and {_spec.max}."
                raise ValueError(msg)
            self._write_registers(_spec.address, int(value))

        prop = property(getter, setter) if spec.writable else property(getter)

        prop.__doc__ = f"{name} ({'read/write' if spec.writable else 'read-only'})" + (
            f" range=[{spec.min}, {spec.max}]" if spec.range else ""
        )

        setattr(cls, name, prop)

    return cls


@register_properties
class Dcm230:
    """Driver for Eastron Dcm230 series energy meters.

    Provides read and write access to Modbus registers via an existing
    `pymodbus.client.ModbusSerialClient` instance. Register definitions are
    dynamically mapped to @property accessors based on `_register_specs`.
    """

    SINGLE_REGISTER = 1
    MAX_REGS = 2

    INPUT_REGISTER = 0x03
    HOLDING_REGISTER = 0x04

    BACKLIT_OPTIONS: ClassVar[list[int]] = [0, 5, 10, 20, 30, 60]
    DCM230_REGISTER_BACKLIT_TIME = 0x003C
    DCM230_REGISTER_RESET_MAX_DMD_AND_PARTIAL_ENERGY = 0xF010
    RESET_MAX_DMD = 0x0000
    RESET_PARTIAL_ENERGY = 0x0003

    _register_specs: Final[dict[str, RegisterSpec]] = {
        "V": RegisterSpec(address=0x0000, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "A": RegisterSpec(address=0x0006, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "W": RegisterSpec(address=0x000C, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "kwh": RegisterSpec(address=0x0048, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "W_dmd": RegisterSpec(address=0x0054, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "W_dmd_peak": RegisterSpec(address=0x0056, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "kwh_tot": RegisterSpec(address=0x0156, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "kwh_partial": RegisterSpec(address=0x0180, count=2, decimals=1, reg_type=INPUT_REGISTER),
        "dmd_period": RegisterSpec(
            address=0x0002,
            count=2,
            range=True,
            min=0,
            max=60,
            writable=True,
            reg_type=HOLDING_REGISTER,
            return_type=int,
        ),
        "network_info": RegisterSpec(
            address=0x0012, count=2, range=True, min=0, max=3, writable=True, reg_type=HOLDING_REGISTER, return_type=int
        ),
        "device_id": RegisterSpec(
            address=0x0014,
            count=2,
            range=True,
            min=1,
            max=247,
            writable=True,
            reg_type=HOLDING_REGISTER,
            return_type=int,
        ),
        "password": RegisterSpec(address=0x0018, count=2, reg_type=HOLDING_REGISTER, return_type=int),
        "baud_rate": RegisterSpec(
            address=0x001C, count=2, range=True, min=0, max=5, writable=True, reg_type=HOLDING_REGISTER, return_type=int
        ),
        "energy_measurement_tool": RegisterSpec(
            address=0xF920, count=2, range=True, min=0, max=3, writable=True, reg_type=HOLDING_REGISTER, return_type=int
        ),
        "serial_number": RegisterSpec(address=0xFC00, count=2, reg_type=HOLDING_REGISTER, return_type=int),
    }

    def __init__(self, device_address: int, client: ModbusSerialClient) -> None:
        """Initialize an Dcm230 driver instance.

        Args:
            device_address: Modbus address for the Dcm230 meter.
            client: A connected `ModbusSerialClient` instance.
        """
        self.device_address = device_address
        self.client = client

    def _read_registers(self, address: int, count: int, reg_type: int) -> list[int]:
        """Safely read input or holding registers from the Modbus device.

        Args:
            address: Starting register address to read.
            count: Number of registers to read.
            reg_type: Input or holding register.

        Returns:
            A list of integer register values.

        Raises:
            ModbusException: If the read operation fails or returns an error.
            ValueError: If register type is incorrect.
        """
        if reg_type == self.INPUT_REGISTER:
            result = self.client.read_input_registers(address=address, count=count, device_id=self.device_address)
        elif reg_type == self.HOLDING_REGISTER:
            result = self.client.read_holding_registers(address=address, count=count, device_id=self.device_address)
        else:
            msg = f"Unsupported reg_type: {reg_type}"
            raise ValueError(msg)

        if result.isError():
            msg = (
                "Failed to read input register. "
                f"device_address={self.device_address} address={address} count={count} result={result}"
            )
            raise ModbusException(msg)
        return result.registers

    def _read_register(self, register_name: str) -> Decimal | int:
        """Read and scale the specified register.

        Args:
            register_name: Name of the register as defined in `_register_specs`.

        Returns:
            A Decimal value representing the scaled register reading.

        Raises:
            ValueError: If register unpacking fails or returns overflow values.
            ModbusException: If Modbus read operation fails.
        """
        spec = self._register_specs[register_name]
        regs = self._read_registers(spec.address, spec.count, spec.reg_type)

        if spec.return_type is Decimal:
            value = Decimal(str(self._unpack(regs, spec.address)))
            return round(value, spec.decimals)
        return self._unpack(regs, spec.address)

    def _write_registers(self, address: int, value: int) -> None:
        """Write to Modbus registers.

        Args:
            address: Register address to write.
            value: Integer value to write to the register.

        Raises:
            ModbusException: If the write operation fails.
        """
        result = self.client.write_registers(address=address, values=[value], device_id=self.device_address)
        if result.isError():
            msg = f"Failed to write to registers. device_address={self.device_address} address={address} value={value}"
            raise ModbusException(msg)

    def _unpack(self, regs: list[int], address: int) -> int:
        """Unpack raw Modbus register data into an integer value.

        Args:
            regs: The list of register values to unpack.
            address: The base register address (used for error reporting).

        Returns:
            The unpacked integer representation of the registers.

        Raises:
            ValueError: If an invalid number of registers is provided or an
            overflow marker is detected.
        """
        # Some devices return only a single register; pad with zero to make
        # it a full 32-bit value so struct.unpack(...) works correctly.
        if len(regs) == self.SINGLE_REGISTER:
            regs.append(0)  # Padd with zero

        if len(regs) != self.MAX_REGS:
            msg = f"Unexpected register count: {len(regs)} for address={address}"
            raise ValueError(msg)

        return struct.unpack(">f", struct.pack(">HH", regs[0], regs[1]))[0]

    def reset_max_dmd(self) -> None:
        """Reset max demand.

        Raises:
            ModbusException: If failed to write to registers.
        """
        self._write_registers(self.DCM230_REGISTER_RESET_MAX_DMD_AND_PARTIAL_ENERGY, self.RESET_MAX_DMD)

    def reset_partial_energy(self) -> None:
        """Reset partial energy.

        Raises:
            ModbusException: If failed to write to registers.
        """
        self._write_registers(self.DCM230_REGISTER_RESET_MAX_DMD_AND_PARTIAL_ENERGY, self.RESET_PARTIAL_ENERGY)

    @property
    def backlit_time(self) -> int:
        """Backlit time.

        Options:
            0, 5, 10, 20, 30, 60 minutes.

        Returns:
            int: Current backlit time value.

        Raises:
            ValueError: If not a specified value.
            ModbusException: If failed to read holding registers.
        """
        regs = self._read_registers(self.DCM230_REGISTER_BACKLIT_TIME, self.MAX_REGS, self.HOLDING_REGISTER)
        value = round(self._unpack(regs, self.DCM230_REGISTER_BACKLIT_TIME))

        if value not in self.BACKLIT_OPTIONS:
            msg = f"Invalid backlit option: {value}. Must be one of: {self.BACKLIT_OPTIONS}"
            raise ValueError(msg)
        return value

    @backlit_time.setter
    def backlit_time(self, value: int) -> None:
        """Backlite time.

        Options:
            0, 5, 10, 20, 30, 60 minutes.

        Args:
            value (int): Set backlit time.

        Raises:
            ModbusException: If failed to write to registers.
            ValueError: If not specified value.
        """
        if value not in self.BACKLIT_OPTIONS:
            msg = f"Invalid backlit option: {value}. Must be one of: {self.BACKLIT_OPTIONS}"
            raise ValueError(msg)
        self._write_registers(self.DCM230_REGISTER_BACKLIT_TIME, value)
