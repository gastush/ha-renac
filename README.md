# ha-renac
Home assistant custom component to support Renac Solar Inverter

## Home Assistant setup
Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder).

Add to your Home-Assistant config:

```yaml
renac:
  username: <username>
  password: <password>
  equipment_serial: <inverter serial number>
```
To date, the following sensors are supporter :
- AC generated power (W)
- Today's total generated power (kWh)
- PV 1 Voltage (V)
- PV 2 Voltage (V)

