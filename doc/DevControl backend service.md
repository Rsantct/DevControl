# DevControl overview

To run DevControl you need:

- prepare your configuration in **`bin/devcontrol/devcontrol.yml`** (see the example file)
- run `bin/devcontrol_srv.py`, this is better done as a system service, see below.
- navigate to `http://your_server_ip:8081`

# The DevControl system service

Prepare the Systemd unit file:

    sudo nano /etc/systemd/system/devcontrol.service

```
[Unit]
Description=Servidor TCP DevControl
After=network.target zigbee2mqtt.service

[Service]
# Ejecutar como el usuario específico
User=shome
Group=shome

# Directorio de trabajo (donde reside el script)
WorkingDirectory=/home/shome/bin/

# Comando para iniciar el script.
# Se recomienda usar la ruta absoluta al intérprete de Python.
# En caso de un entorno virtual poner algo como /home/shome/venv/bin/python
ExecStart=/usr/bin/python3 /home/shome/bin/devcontrol_srv.py

# Reiniciar automáticamente si el script falla
Restart=always
RestartSec=10

# Captura la salida estándar y de errores en el log del sistema
#StandardOutput=journal
#StandardError=journal
# no imprimir constantantemente, pero los errores seguirán en journalctrl:
StandardOutput=null
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

Recargar systemd para que conozca el nuevo servicio:

`sudo systemctl daemon-reload`

Habilitar para que arranque con el sistema:

`sudo systemctl enable devcontrol.service`

Arrancar el servicio ahora mismo:

`sudo systemctl start devcontrol.service`

Comprobar:
```
sudo systemctl status devcontrol.service
● devcontrol.service - Servidor TCP DevControl
     Loaded: loaded (/etc/systemd/system/devcontrol.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-02-06 23:19:30 CET; 8s ago
   Main PID: 23021 (python3)
      Tasks: 3 (limit: 1568)
        CPU: 1.126s
     CGroup: /system.slice/devcontrol.service
             └─23021 /usr/bin/python3 /home/shome/bin/devcontrol_srv.py

Feb 06 23:19:30 rpi3clac systemd[1]: Started devcontrol.service - Servidor TCP DevControl.
```
