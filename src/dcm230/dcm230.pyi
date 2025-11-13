from decimal import Decimal

from pymodbus.client import ModbusSerialClient

class RegisterSpec:
    address: int
    count: int
    reg_type: int
    decimals: int = 0
    range: bool = False
    min: int = 0
    max: int = 0x7FFFFFFF
    writable: bool = False
    return_type: type[int | Decimal] = ...

    def register_properties(self) -> None: ...

class Dcm230:
    RESET_MAX_DMD: int
    RESET_PARTIAL_ENERGY: int
    DCM230_REGISTER_RESET_MAX_DMD_AND_PARTIAL_ENERGY: int
    DCM230_REGISTER_BACKLIT_TIME: int
    INPUT_REGISTER: int
    HOLDING_REGISTER: int
    _register_specs: RegisterSpec

    def __init__(self, device_address: int, client: ModbusSerialClient) -> None: ...
    V: Decimal
    A: Decimal
    W: Decimal
    kwh: Decimal
    W_dmd: Decimal
    W_dmd_peak: Decimal
    kwh_tot: Decimal
    kwh_partial: Decimal
    dmd_period: Decimal
    backlit_time: int
    network_info: int
    device_id: int
    password: int
    baud_rate: int
    energy_measurement_tool: int
    serial_number: int

    def _unpack(self, registers: list[int], address: int) -> int: ...
    def _write_registers(self, address: int, value: int) -> None: ...
    def _read_register(self, register_name: str) -> Decimal | int: ...
    def _read_input_registers(self, address: int, count: int) -> list[int]: ...
    def _read_registers(self, address: int, count: int, reg_type: int) -> list[int]: ...
    def reset_max_dmd(self) -> None: ...
    def reset_partial_energy(self) -> None: ...
