# python-dcm230

Driver for Eastron DCM230 DC Energy Meters using Modbus RTU.

## Get started

### Prerequisites

* Install [Python (>=3.10)](https://www.python.org/downloads/)
* Install [git](https://git-scm.com/downloads)
* Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Setup development environment

Clone the repository:

```sh
git clone git@github.com:id8-engineering/python-dcm230.git
```

Change directory:

```sh
cd python-dcm230
```

Run pre-commit tests:

```sh
uv run pre-commit run -a
```

Build package:

```sh
uv build
```
