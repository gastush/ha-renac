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
- PV 1,2 Voltage (V)
- PV 1,2 Current (A)
- PV 1,2 Power (W)
- R,S,T Voltage (V)
- R,S,T Current (A)
- Total generated power (kWh)
