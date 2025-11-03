# ruff: noqa: N802
"""Driver class for Dcm230."""

from decimal import Decimal
import struct
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException


class Dcm230:
    """Driver for Carlo Gavazzi Dcm230
    series energy meters.

      This class provides read and write access to Modbus registers
      via a connected `pymodbus.client.ModbusSerialClient` instance.

      Attributes:
          device_address (int): Modbus address of the target device.
          client (ModbusSerialClient): Connected Modbus client.
    """

    INT16_REG_COUNT = 1
    INT32_REG_COUNT = 2

    DCM230_REGISTER_V = 0x0000

    def __init__(self, device_address: int, client: ModbusSerialClient) -> None:
        """Initialize an Dcm230 driver instance with an existing Modbus client.

        Args:
            device_address: Modbus address for the Dcm230
           meter.
            client: An initialized ModbusSerialClient instance to use for communication.
        """
        self.device_address = device_address
        self.client = client

    def _read_input_registers(self, address: int, count: int) -> list[int]:
        """Read input registers.

        Internal helper to read Modbus registers safely.

        Args:
            address: Register address to read from.
            count: Number of register to read from.

        Returns:
            list of registers.

        Raises:
            ModbusException: If read operation fails.
        """
        result = self.client.read_input_registers(
            address=address, count=count, device_id=self.device_address
        )
        if result.isError():
            msg = (
                "Failed to read input register. "
                f"device_address={self.device_address} address={address} count={count} result={result} "
            )
            raise ModbusException(msg)
        return result.registers

    def _write_register(self, address: int, value: int) -> None:
        """Write to register.

        Internal helper to write to single register.

        Args:
            address: Register to write to.
            value: Value to write the given register with.

        Raises:
            ModbusException: If write operation fails.
        """
        result = self.client.write_register(
            address=address, value=value, device_id=self.device_address
        )

        if result.isError():
            msg = (
                "Failed to write to single register: "
                f"device_address={self.device_address} address={address} count={value}"
            )
            raise ModbusException(msg)

    def _unpack(self, regs: list[int], address: int) -> int:
        """Unpack raw Modbus register data into an integer value.

        Supports both 16-bit and 32-bit register combinations and performs
        overflow detection for "EEE" values reported by the meter.

        Args:
            regs: The list of register values to unpack.
            address: The base register address (used for error reporting).

        Returns:
            The unpacked integer representation of the registers.

        Raises:
            ValueError: If an invalid number of registers is provided or an
                overflow marker is detected.
        """
        if len(regs) == self.INT16_REG_COUNT:
            value = regs[0]
            return value

        if len(regs) == self.INT32_REG_COUNT:
            value = struct.unpack(">f", struct.pack(">HH", regs[0], regs[1]))[0]
            return value
        msg = f"Unexpected register count: {len(regs)} for address={address}"
        raise ValueError(msg)

    @property
    def V(self) -> Decimal:
        """Voltage (V).

        Returns:
            Decimal: Current voltage value.

        Raises:
            ValueError: If input is at max value or above.
            ModbusException: If failed to read input register.
        """
        regs = self._read_input_registers(self.DCM230_REGISTER_V, self.INT32_REG_COUNT)
        value = Decimal(self._unpack(regs, self.DCM230_REGISTER_V))
        return round(value, 1)
