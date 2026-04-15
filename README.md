# ha-renac
Home assistant custom component to support Renac Solar Inverter
Only On-Grid type of Inverters (R3-xK-DT) are supported. The NV3-HV kind of Hybrid Inverter won't work.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)]([https://www.buymeacoffee.com/gastush](https://www.buymeacoffee.com/gastush))

## Breaking changes as from version 0.1.x
As from version 0.1.3, the configuration is now done through the UI. Remove the `renac:` section from the `configuration.yml` and configure the component from the UI directly.
The name of the various sensors also changed to include the name of the equipment (for future support of multiple equipements)
This version also includes a tentative support for the Hybrid Inverters. This hasn't been tested since I don't have access to it. I added the sensors that were proposed in one of the reported issues.
The session management should also be a bit more robust. The whole logic to interact with the Renac back-end server has been moved to the pyrenac project and has also been updated to use `async` logic everywhere. This is a requirement if we want to include this component as part of the official intergrations.
This version also includes a service to sync the recorder data (to fix wrong/missing long term statistics). So far all my attempts where rather unsuccessful in the way that the imported data looked good, but all subsequent data were broken... so don't use it unless you want to break everything have have to fix the recorder database by hand...


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
