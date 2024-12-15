# ha-renac
Home assistant custom component to support Renac Solar Inverter
Only On-Grid type of Inverters (R3-xK-DT) are supported. The NV3-HV kind of Hybrid Inverter won't work.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)]([https://www.buymeacoffee.com/gastush](https://www.buymeacoffee.com/gastush))

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
- R,S,T Frquency (Hz)
- Total generated power (kWh)
