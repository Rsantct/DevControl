# Zigbee devices

This is intended to manage Zigbeee smart lights, here we we use IKEA TRADFRI devices.

## General view of needed componentes:

- Zigbee devices: lightbulbs, etc
- USB Zigbee adapter, for example: Sonoff ZBDongle-P (or E)  
- Zigbee2MQTT: the interface between your Zigbee network and the MQTT broker
- An standard MQTT broker server, we use Mosquitto.
- paho-mqtt: a Python module for the MQTT comms protocol
- This DevControl software

## Features:
- Simple ON/OFF management based on predefined 'scenes' under the zigbee2mqtt web interface. 
- Also you can easily modify the brightness and set a timer to automatically switch off
- `crontab` integration for schedulling switch on/off

All commands are sent to or received from the MQTT broker.

## Environment

MQTT server Mosquitto is installed from the regular Debian package.

The rest of the software is kept under a dedicated Linux user, here we use **`/home/shome`**

    shome@rpi3clac:~ $ tree /home/shome
    /home/shome
    ├── bin
    │   │
    │   ├── devcontrol
    │   │   │
    │   │   ├── devcontrol.py
    │   │   │
    │   │   └── modules
    │   │       ├── zigbees.py       (our zigbee backend for the DevControl web frontend)
    │   │       │
    │   │       └── devices_mod/
    │   │           └── zigbee.py    (our low level zigbee Python module)
    │   │
    │   ├── zigbee_control.py  (for testing purposes)
    │   ...
    │
    └── zigbee2mqtt  (The Zigbee2MQTT server package is installed here)
        │
        ├── data
        │   └── configuration.yaml    (the only file we need to edit)
        ...


## 1. Hardware: Zigbee 3.0 USB Dongle Plus V2 model ZBDongle-E

    [Tue Jan 27 11:28:34 2026] usb 1-1.1.3.4: new full-speed USB device number 9 using dwc_otg
    [Tue Jan 27 11:28:35 2026] usb 1-1.1.3.4: New USB device found, idVendor=10c4, idProduct=ea60, bcdDevice= 1.00
    [Tue Jan 27 11:28:35 2026] usb 1-1.1.3.4: New USB device strings: Mfr=1, Product=2, SerialNumber=3
    [Tue Jan 27 11:28:35 2026] usb 1-1.1.3.4: Product: Sonoff Zigbee 3.0 USB Dongle Plus V2
    [Tue Jan 27 11:28:35 2026] usb 1-1.1.3.4: Manufacturer: Itead
    [Tue Jan 27 11:28:35 2026] usb 1-1.1.3.4: SerialNumber: 9eebd3eafdc2ef1181e1e5b08048b910
    [Tue Jan 27 11:28:35 2026] usbcore: registered new interface driver cp210x
    [Tue Jan 27 11:28:35 2026] usbserial: USB Serial support registered for cp210x
    [Tue Jan 27 11:28:35 2026] cp210x 1-1.1.3.4:1.0: cp210x converter detected
    [Tue Jan 27 11:28:35 2026] usb 1-1.1.3.4: cp210x converter now attached to ttyUSB1

## 2. Install MQTT server: Mosquitto (system service)

    # servidor (broker)
    sudo apt install mosquitto              
    # herramientas de línea de comandos que te permitirán probar 
    # si tus scripts de Python están enviando datos correctamente
    sudo apt install mosquitto-clients

    sudo nano /etc/mosquitto/conf.d/default.conf
        listener 1883
        allow_anonymous true

    sudo systemctl enable mosquitto
    sudo systemctl restart mosquitto
    sudo systemctl status mosquitto

Test de comunicación

    Terminal A
    mosquitto_sub -h localhost -t "zigbee2mqtt/luz_ikea"

    Terminal B
    mosquitto_pub -h localhost -t "zigbee2mqtt/luz_ikea" -m '{"state": "ON"}'

    --> ver mensajes subscription en Terminal A

## 3. Zigbee2MQTT (system service)

El software que traduce Zigbee a mensajes de texto (JSON) que Python puede leer.

La instalación (`git clone ...`) la haremos en un subdirectorio de nuestro usuario Linux:

**`/home/shome/zigbee2mqtt/`**
  
### 3.1 Install Zigbee2MQTT

    # NodeJS    **OjO a la versión**
    sudo apt list nodejs
    nodejs/oldstable,now 18.20.4+dfsg-1~deb12u1+rpi1 armhf [installed]

    # OJO verion 18 es VIEJUNA, necesitamos debian nueva:
    sudo apt purge nodejs npm -y
    sudo apt autoremove -y

    # Añadir repositorio de Node.js (versión 20.x recomendada)
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    ...
    ...
    2026-01-27 13:12:40 - Repository configured successfully.

    # Comprobamos
    apt list nodejs
    nodejs/nodistro 20.19.1-1nodesource1 armhf

    # Instalamos NodeJS y más cositas por si no estaban
    sudo apt-get install -y nodejs git make g++ gcc
    $ node --version
    v20.19.1

    # Instalamos gestor de paketes moderno 'pnpm'
    sudo npm install -g pnpm    # gestor de paquetes más rápido que npm

    # Clonar Zigbee2MQTT
    mkdir zigbee2mqtt
    git clone --depth 1 https://github.com/Koenkk/zigbee2mqtt.git zigbee2mqtt
    cd zigbee2mqtt

    # Generar el archivo package-lock.json e instalar dependencias
    pnpm install

### 3.2 Configure Zigbee2MQTT

    # Permiso de acceso a /dev/serial/ para el usuario (grupo dialout)
    sudo usermod -a -G dialout <USUARIO>

    # Ver el dispositivo Zigbee en los serial de Linux:
    ls -l /dev/serial/by-id
    lrwxrwxrwx 1 root root 13 Jan 27 11:54 usb-Itead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_V2_9eebd3eafdc2ef1181e1e5b08048b910-if00-port0 -> ../../ttyUSB1


    # Archivo de configuración:

    nano zigbee2mqtt/data/configuration.yaml

        # Configuración básica
        homeassistant: false

        # Conexión al servidor MQTT que instalamos antes
        mqtt:
          base_topic: zigbee2mqtt
          server: 'mqtt://localhost'

        # Configuración del adaptador Sonoff
        serial:
          port: /dev/serial/by-id/AQUÍ_PEGA_TU_RUTA_COPIADA
          adapter: ezsp # Solo si usas el modelo "E". Para el modelo "P" no es obligatorio ponerlo.

        # Interfaz web para ver tus dispositivos (opcional pero muy útil)
        frontend:
          port: 8080

### 3.3 Run and pair devices

Iniciamos el servidor Zigbee2MQTT

    npm start

    > zigbee2mqtt@2.7.2 start
    > node index.js

    Starting Zigbee2MQTT without watchdog.
    Building Zigbee2MQTT... (initial build), finished  LA PRIMERA VEZ ESTO TARDA DECENAS DE SEGUNDOS EN RPI3
    ...
    ...
    [2026-01-27 17:51:31] info:     z2m: Zigbee2MQTT started!


**web del servidor Zigbee2MQTT** con un navegador:

        http://rpi3clac.local:8090

y darle al botoncito de permitir JOIN (inicia una cuenta atrás de unos segundos como un router WiFi)

    [2026-01-27 17:39:25] info:     z2m: Zigbee: allowing new devices to join.
    [2026-01-27 17:39:25] info:     z2m:mqtt: MQTT publish: topic 'zigbee2mqtt/bridge/response/permit_join', payload '{"data":{"time":254},"status":"ok","transaction":"w2vhh-3"}'


A- Emparejar el **driver IKEA TRADFRI**

Haciendo reset con clip durante 5~10 seg, veremos por la consola:


    [2026-01-27 17:39:43] info:     zh:controller: Interview for '0x348d13fffe724869' started
    [2026-01-27 17:39:43] info:     z2m: Device '0x348d13fffe724869' joined

B- Emparejar una bombilla **TRADFRI LED**

Haciendo 6 encendidos consecutivos a ritmo tranquilo la dejamos encendida en el sexto:

    [31/1/2026, 1:00:33] z2m: Device '0x8c8b48fffe23f09e' is supported, identified as: IKEA TRADFRI bulb E12/E14, white spectrum, globe, opal, 450/470 lm (LED2101G4)
    [31/1/2026, 1:00:33] z2m: Configuring '0x8c8b48fffe23f09e'
    [31/1/2026, 1:00:33] z2m:mqtt: MQTT publish: topic 'zigbee2mqtt/bridge/event', payload '{"data":{"definition":{"description":"TRADFRI bulb E12/E14, white spectrum, globe, opal, 450/470 lm","exposes":[{"features":[{"access":7,"description":"On/off state of this light","label":"State","name":"state","property":"state","type":"binary","value_off":"OFF","value_on":"ON","value_toggle":"TOGGLE"},{"access":7,"description":"Brightness of this light","label":"Brightness","name":"brightness","property":"brightness","type":"numeric","value_max":254,"value_min":0},{"access":7,"description":"Color temperature of this light","label":"Color temp","name":"color_temp","presets":[{"description":"Coolest temperature supported","name":"coolest","value":250},{"description":"Cool temperature (250 mireds / 4000 Kelvin)","name":"cool","value":250},{"description":"Neutral temperature (370 mireds / 2700 Kelvin)","name":"neutral","value":370},{"description":"Warm temperature (454 mireds / 2200 Kelvin)","name":"warm","value":454},{"description":"Warmest temperature supported","name":"warmest","value":454}],"property":"color_temp","type":"numeric","unit":"mired","value_max":454,"value_min":250},{"access":7,"description":"Color temperature after cold power on of this light","label":"Color temp startup","name":"color_temp_startup","presets":[{"description":"Coolest temperature supported","name":"coolest","value":250},{"description":"Cool temperature (250 mireds / 4000 Kelvin)","name":"cool","value":250},{"description":"Neutral temperature (370 mireds / 2700 Kelvin)","name":"neutral","value":370},{"description":"Warm temperature (454 mireds / 2200 Kelvin)","name":"warm","value":454},{"description":"Warmest temperature supported","name":"warmest","value":454},{"description":"Restore previous color_temp on cold power on","name":"previous","value":65535}],"property":"color_temp_startup","type":"numeric","unit":"mired","value_max":454,"value_min":250},{"access":7,"description":"Configure genLevelCtrl","features":[{"access":7,"description":"this setting can affect the \"on_level\", \"current_level_startup\" or \"brightness\" setting","label":"Execute if off","name":"execute_if_off","property":"execute_if_off","type":"binary","value_off":false,"value_on":true},{"access":7,"description":"Defines the desired startup level for a device when it is supplied with power","label":"Current level startup","name":"current_level_startup","presets":[{"description":"Use minimum permitted value","name":"minimum","value":"minimum"},{"description":"Use previous value","name":"previous","value":"previous"}],"property":"current_level_startup","type":"numeric","value_max":254,"value_min":1}],"label":"Level config","name":"level_config","property":"level_config","type":"composite"}],"type":"light"},{"access":2,"description":"Triggers an effect on the light (e.g. make light blink for a few seconds)","label":"Effect","name":"effect","property":"effect","type":"enum","values":["blink","breathe","okay","channel_change","finish_effect","stop_effect"]},{"access":7,"category":"config","description":"Controls the behavior when the device is powered on after power loss","label":"Power-on behavior","name":"power_on_behavior","property":"power_on_behavior","type":"enum","values":["off","on","toggle","previous"]},{"access":7,"category":"config","description":"Advanced color behavior","features":[{"access":2,"description":"Controls whether color and color temperature can be set while light is off","label":"Execute if off","name":"execute_if_off","property":"execute_if_off","type":"binary","value_off":false,"value_on":true}],"label":"Color options","name":"color_options","property":"color_options","type":"composite"},{"access":2,"category":"config","description":"Initiate device identification","label":"Identify","name":"identify","property":"identify","type":"enum","values":["identify"]},{"access":1,"category":"diagnostic","description":"Link quality (signal strength)","label":"Linkquality","name":"linkquality","property":"linkquality","type":"numeric","unit":"lqi","value_max":255,"value_min":0}],"model":"LED2101G4","options":[{"access":2,"description":"Controls the transition time (in seconds) of on/off, brightness, color temperature (if applicable) and color (if applicable) changes. Defaults to `0` (no transition).","label":"Transition","name":"transition","property":"transition","type":"numeric","value_min":0,"value_step":0.1},{"access":2,"description":"Whether to unfreeze IKEA lights (that are known to be frozen) before issuing a command, false: no unfreeze support, true: unfreeze support (default true).","label":"Unfreeze support","name":"unfreeze_support","property":"unfreeze_support","type":"binary","value_off":false,"value_on":true},{"access":2,"description":"When enabled colors will be synced, e.g. if the light supports both color x/y and color temperature a conversion from color x/y to color temperature will be done when setting the x/y color (default true).","label":"Color sync","name":"color_sync","property":"color_sync","type":"binary","value_off":false,"value_on":true},{"access":2,"description":"Sets the duration of the identification procedure in seconds (i.e., how long the device would flash).The value ranges from 1 to 30 seconds (default: 3).","label":"Identify timeout","name":"identify_timeout","property":"identify_timeout","type":"numeric","value_max":30,"value_min":1},{"access":2,"description":"State actions will also be published as 'action' when true (default false).","label":"State action","name":"state_action","property":"state_action","type":"binary","value_off":false,"value_on":true}],"source":"native","supports_ota":true,"vendor":"IKEA"},"friendly_name":"0x8c8b48fffe23f09e","ieee_address":"0x8c8b48fffe23f09e","status":"successful","supported":true},"type":"device_interview"}'
    [31/1/2026, 1:00:33] z2m: Successfully configured '0x8c8b48fffe23f09e'

    B2 - Otra:
    [31/1/2026, 1:14:36] z2m: Successfully interviewed '0x8c8b48fffe7a867c', device has successfully been paired
    [31/1/2026, 1:14:36] z2m: Device '0x8c8b48fffe7a867c' is supported, identified as: IKEA TRADFRI bulb E12/E14, white spectrum, globe, opal, 450/470 lm (LED2101G4)
    [31/1/2026, 1:14:36] z2m: Configuring '0x8c8b48fffe7a867c'
    [31/1/2026, 1:14:36] z2m:mqtt: MQTT publish: topic 'zigbee2mqtt/bridge/event', payload '{"data":{"definition":{"description":"TRADFRI bulb E12/E14, white spectrum, globe, opal, 450/470 lm","exposes":[{"features":[{"access":7,"description":"On/off state of this light","label":"State","name":"state","property":"state","type":"binary","value_off":"OFF","value_on":"ON","value_toggle":"TOGGLE"},{"access":7,"description":"Brightness of this light","label":"Brightness","name":"brightness","property":"brightness","type":"numeric","value_max":254,"value_min":0},{"access":7,"description":"Color temperature of this light","label":"Color temp","name":"color_temp","presets":[{"description":"Coolest temperature supported","name":"coolest","value":250},{"description":"Cool temperature (250 mireds / 4000 Kelvin)","name":"cool","value":250},{"description":"Neutral temperature (370 mireds / 2700 Kelvin)","name":"neutral","value":370},{"description":"Warm temperature (454 mireds / 2200 Kelvin)","name":"warm","value":454},{"description":"Warmest temperature supported","name":"warmest","value":454}],"property":"color_temp","type":"numeric","unit":"mired","value_max":454,"value_min":250},{"access":7,"description":"Color temperature after cold power on of this light","label":"Color temp startup","name":"color_temp_startup","presets":[{"description":"Coolest temperature supported","name":"coolest","value":250},{"description":"Cool temperature (250 mireds / 4000 Kelvin)","name":"cool","value":250},{"description":"Neutral temperature (370 mireds / 2700 Kelvin)","name":"neutral","value":370},{"description":"Warm temperature (454 mireds / 2200 Kelvin)","name":"warm","value":454},{"description":"Warmest temperature supported","name":"warmest","value":454},{"description":"Restore previous color_temp on cold power on","name":"previous","value":65535}],"property":"color_temp_startup","type":"numeric","unit":"mired","value_max":454,"value_min":250},{"access":7,"description":"Configure genLevelCtrl","features":[{"access":7,"description":"this setting can affect the \"on_level\", \"current_level_startup\" or \"brightness\" setting","label":"Execute if off","name":"execute_if_off","property":"execute_if_off","type":"binary","value_off":false,"value_on":true},{"access":7,"description":"Defines the desired startup level for a device when it is supplied with power","label":"Current level startup","name":"current_level_startup","presets":[{"description":"Use minimum permitted value","name":"minimum","value":"minimum"},{"description":"Use previous value","name":"previous","value":"previous"}],"property":"current_level_startup","type":"numeric","value_max":254,"value_min":1}],"label":"Level config","name":"level_config","property":"level_config","type":"composite"}],"type":"light"},{"access":2,"description":"Triggers an effect on the light (e.g. make light blink for a few seconds)","label":"Effect","name":"effect","property":"effect","type":"enum","values":["blink","breathe","okay","channel_change","finish_effect","stop_effect"]},{"access":7,"category":"config","description":"Controls the behavior when the device is powered on after power loss","label":"Power-on behavior","name":"power_on_behavior","property":"power_on_behavior","type":"enum","values":["off","on","toggle","previous"]},{"access":7,"category":"config","description":"Advanced color behavior","features":[{"access":2,"description":"Controls whether color and color temperature can be set while light is off","label":"Execute if off","name":"execute_if_off","property":"execute_if_off","type":"binary","value_off":false,"value_on":true}],"label":"Color options","name":"color_options","property":"color_options","type":"composite"},{"access":2,"category":"config","description":"Initiate device identification","label":"Identify","name":"identify","property":"identify","type":"enum","values":["identify"]},{"access":1,"category":"diagnostic","description":"Link quality (signal strength)","label":"Linkquality","name":"linkquality","property":"linkquality","type":"numeric","unit":"lqi","value_max":255,"value_min":0}],"model":"LED2101G4","options":[{"access":2,"description":"Controls the transition time (in seconds) of on/off, brightness, color temperature (if applicable) and color (if applicable) changes. Defaults to `0` (no transition).","label":"Transition","name":"transition","property":"transition","type":"numeric","value_min":0,"value_step":0.1},{"access":2,"description":"Whether to unfreeze IKEA lights (that are known to be frozen) before issuing a command, false: no unfreeze support, true: unfreeze support (default true).","label":"Unfreeze support","name":"unfreeze_support","property":"unfreeze_support","type":"binary","value_off":false,"value_on":true},{"access":2,"description":"When enabled colors will be synced, e.g. if the light supports both color x/y and color temperature a conversion from color x/y to color temperature will be done when setting the x/y color (default true).","label":"Color sync","name":"color_sync","property":"color_sync","type":"binary","value_off":false,"value_on":true},{"access":2,"description":"Sets the duration of the identification procedure in seconds (i.e., how long the device would flash).The value ranges from 1 to 30 seconds (default: 3).","label":"Identify timeout","name":"identify_timeout","property":"identify_timeout","type":"numeric","value_max":30,"value_min":1},{"access":2,"description":"State actions will also be published as 'action' when true (default false).","label":"State action","name":"state_action","property":"state_action","type":"binary","value_off":false,"value_on":true}],"source":"native","supports_ota":true,"vendor":"IKEA"},"friendly_name":"0x8c8b48fffe7a867c","ieee_address":"0x8c8b48fffe7a867c","status":"successful","supported":true},"type":"device_interview"}'
    [31/1/2026, 1:14:36] z2m:mqtt: MQTT publish: topic 'zigbee2mqtt/salon_libreria_izq', payload '{"brightness":83,"color_mode":"color_temp","color_temp":354,"linkquality":112,"state":"ON","update":{"installed_version":16842784,"latest_version":16842784,"state":"idle"}}'
    [31/1/2026, 1:14:36] z2m: Successfully configured '0x8c8b48fffe7a867c'

### Zigbee2MQTT as system service

    sudo nano /etc/systemd/system/zigbee2mqtt.service

        [Unit]
        Description=servicio zigbee2mqtt
        After=network.target mosquitto.service

        [Service]
        Environment=NODE_ENV=production
        # Ajusta el usuario si es distinto a 'shome'
        User=shome
        Group=shome
        WorkingDirectory=/home/shome/zigbee2mqtt
        # Usamos el comando directo de node para mayor estabilidad
        ExecStart=/usr/bin/node index.js
        Restart=always
        RestartSec=10s
        # no imprimir constantantemente, pero los errores seguirán en journalctrl:
        StandardOutput=null
        StandardError=inherit

        [Install]
        WantedBy=multi-user.target


    # Recargar systemd para que conozca el nuevo servicio
    sudo systemctl daemon-reload

    # Habilitar para que arranque con el sistema
    sudo systemctl enable zigbee2mqtt.service

    # Arrancar el servicio ahora mismo
    sudo systemctl start zigbee2mqtt.service

    # Comprobar
    sudo systemctl status zigbee2mqtt.service
    ● zigbee2mqtt.service - servicio zigbee2mqtt
         Loaded: loaded (/etc/systemd/system/zigbee2mqtt.service; enabled; preset: enabled)
         Active: active (running) since Tue 2026-01-27 18:29:35 CET; 2s ago
       Main PID: 17951 (node)
          Tasks: 7 (limit: 1568)
            CPU: 3.213s
         CGroup: /system.slice/zigbee2mqtt.service
                 └─17951 /usr/bin/node index.js

    Jan 27 18:29:35 rpi3clac systemd[1]: Started zigbee2mqtt.service - servicio zigbee2mqtt.

**WEB INTERFACE**

    http://rpi3clac.local:8090

**Para ver logs en tiempo real**

    journalctl -u zigbee2mqtt.service -f

# How to ensure the light bulbs behavior after a power outage

To determine the behavior of light bulbs when they receive power after a power outage you can use the WEB INTERFACE

You can also use the terminal:

    shome@rpi3clac:~ $ zigbee_control.py -dev='estudio_billy_1' power=off
    true
    shome@rpi3clac:~ $ zigbee_control.py -dev='estudio_billy_1' state
    {"brightness": 25, "level_config": {"current_level_startup": 121}, "linkquality": 200, "power_on_behavior": "off", "state": "off", "update": {"installed_version": 16777220, "latest_version": 16777220, "state": "idle"}}
    
# How to ensure switching OFF daily

Zigbee light devices has not scheduling support, so we use the system user `crontab`.

You can schedule jobs under `devcontrol.yml`, see the provided sample file. The system will autmatically maintain jobs under your `crontab`

Or you can prepare manually cron jobs:
    
    shome@rpi3clac:~ $ crontab -l
    # m h  dom mon dow   command
    
    00 02 *  *  *  mosquitto_pub -h localhost -t "zigbee2mqtt/estudio_billy_1/set" -m '{"state": "off"}'
    00 02 *  *  *  mosquitto_pub -h localhost -t "zigbee2mqtt/salon_libreria_izq/set" -m '{"state": "off"}'
    00 02 *  *  *  mosquitto_pub -h localhost -t "zigbee2mqtt/salon_libreria_der/set" -m '{"state": "off"}'



