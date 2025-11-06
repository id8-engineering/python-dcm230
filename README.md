[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/id8-engineering/python-dcm230/badge)](https://scorecard.dev/viewer/?uri=github.com/id8-engineering/python-dcm230)

## python-dcm230

python-dcm230 provides a simple, Pythonic interface for reading and writing data 
from Eastron DCM230 DC meters over Modbus RTU. It builds on top 
of [pymodbus](https://pypi.org/project/pymodbus/).

## Example usage:

```python
from dcm230 import Dcm230
from pymodbus.client import ModbusSerialClient

# Configure the Modbus client
client = ModbusSerialClient(
   port="COM3",  # or "/dev/ttyUSB0" on Linux
   baudrate=9600,
   parity="E",
   stopbits=1,
   bytesize=8,
   timeout=1,
)

# Device Modbus address
device_address = 1

# Initialize the Dcm230 driver
meter = Dcm230(device_address=device_address, client=client)

# Read voltage
voltage = meter.V
print(f"Voltage: {voltage} V")
```

## Report issues

If you run into problems, you can ask for help in our [issue tracker](https://github.com/id8-engineering/python-dcm230/issues) on GitHub.

## Contributing
See [CONTRIBUTING.MD](https://github.com/id8-engineering/python-dcm230/blob/main/CONTRIBUTING.MD) and [DEVELOPMENT.MD](https://github.com/id8-engineering/python-dcm230/blob/main/DEVELOPMENT.MD).
