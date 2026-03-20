# pyteslaconnectpk

[![PyPI](https://img.shields.io/pypi/v/pyteslaconnectpk)](https://pypi.org/project/pyteslaconnectpk/)
[![License](https://img.shields.io/github/license/uppaljs/pyteslaconnectpk)](LICENSE)

Python API client for **Tesla Connect Pakistan** geyser and inverter devices.

> **Disclaimer:** This is an **unofficial**, community-built library. The author has **no affiliation** with Tesla Industries Pakistan (https://tesla-pv.com). All product names, logos, and brands are property of their respective owners.

## Installation

```bash
pip install pyteslaconnectpk
```

## Quick Start

```python
from pyteslaconnectpk import TeslaConnectApi

client = TeslaConnectApi("03XXXXXXXXX", "your_password")
client.sign_in()

print(f"Logged in as {client.user_name}")
print(f"Devices: {len(client.devices)}")

# Get geyser details
for device in client.devices:
    if device["type_id"] == 2:  # Geyser
        details = client.get_geyser_details(device["device_id"])
        print(f"Temperature: {details['curr_temp']}°C")

# Control the geyser
client.set_geyser_temp_limit("device_id", 55)
client.set_geyser_boost("device_id", True)
```

## API Reference

### Authentication

| Method | Description |
|--------|-------------|
| `sign_in()` | Authenticate and obtain a session token |
| `change_password(new_password)` | Change the account password |

### Devices

| Method | Description |
|--------|-------------|
| `refresh_devices()` | Re-login to refresh the device list |
| `add_device(device_id, name)` | Register a new device |
| `delete_device(device_id, name)` | Remove a device |

### Geyser

| Method | Description |
|--------|-------------|
| `get_geyser_details(device_id)` | Get geyser status (temp, mode, timers, etc.) |
| `set_geyser_boost(device_id, enabled)` | Toggle boost mode |
| `set_geyser_mode(device_id, curr_mode, user_mode)` | Set operating mode |
| `set_geyser_temp_limit(device_id, temp_limit)` | Set target temperature |
| `set_geyser_timer(device_id, times)` | Set hourly schedule |
| `set_geyser_two_hour_mode(device_id, enabled)` | Toggle two-hour mode |
| `set_geyser_vacation_mode(device_id, enabled)` | Toggle vacation mode |

### Inverter

| Method | Description |
|--------|-------------|
| `get_inverter_details(device_id)` | Get inverter status |

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEVICE_TYPE_GEYSER` | 2 | Geyser device type |
| `DEVICE_TYPE_INVERTER` | 1 | Inverter device type |
| `GEYSER_MODE_GAS` | 0 | Gas mode |
| `GEYSER_MODE_ELECTRICITY` | 1 | Electric mode |
| `GEYSER_MODE_AUTOMATIC` | 2 | Automatic mode |
| `GEYSER_MODE_SOLAR_ENABLED` | 3 | Solar enabled |
| `GEYSER_MODE_SOLAR_DISABLED` | 4 | Solar disabled |

### Exceptions

| Exception | When |
|-----------|------|
| `TeslaConnectAuthError` | Invalid credentials or expired session |
| `TeslaConnectApiError` | Connection failure, timeout, or HTTP error |

## Used By

- [tesla-pakistan-hacs](https://github.com/uppaljs/tesla-pakistan-hacs) — Home Assistant custom integration

## License

MIT
