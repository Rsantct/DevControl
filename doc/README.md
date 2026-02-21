# Requirements

## A SoC computer

Like Raspberry Pim, any model

## Software packages

### Python 3

In a recent version.

Modules needed:

    sudo apt install python3-yaml python3-crontab python3-requests python3-paho-mqtt

### Node.js

The web server needs Node.js

    sudo apt update && sudo apt install nodejs npm

On the first time, once you have this repo under your `~/bin/` folder, you'll need to prepare the Node.js modules (Express)

    cd bin/devcontrol/web
    npm install

This will create a new sub-directory `node_modules`:

    bin/devcontrol/web
    ├── node_modules            <<<<<
    ├── package.json
    ├── public
    └── web-server.js

#### testing the web server

Navigate to http://YOURSERVERHOSTNAME.local:8081

Run in a terminal:

    cd bin/devcontrol/web
    node web-server.js -v
    (verbose mode)
    Node.js server active at port 8081
    Reading config at: /home/shome/bin/devcontrol/devcontrol.yml
    Rx: hello
    Tx: hi!


### Download the DevControl app

    mkdir -p ~/bin
    mkdir -p ~/Downloads
    cd ~/Downnloads
    wget https://github.com/Rsantct/DevControl/archive/refs/heads/main.zip
    unzip main.zip
    cp -r DevControl-main/bin/* ~/bin/

## The DevControl backend service

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



## The DevControl web service

The web server will run as a user Systemd service

`sudo nano /etc/systemd/system/devcontrol-web.service`


    [Unit]
    Description=Servidor WEB DevControl con Node.js
    After=network-online.target
    Wants=network-online.target
    
    [Service]
    User=shome
    Group=shome
    WorkingDirectory=/home/shome/bin/devcontrol/web
    ExecStart=/usr/bin/node /home/shome/bin/devcontrol/web/web-server.js
    Restart=always
    RestartSec=5
    StandardOutput=inherit
    StandardError=inherit
    
    [Install]
    WantedBy=multi-user.target
    

```
sudo systemctl daemon-reload
sudo systemctl enable devcontrol-web.service
sudo systemctl start devcontrol-web.service
```
To check:

    sudo systemctl status devcontrol-web.service

To see logs in real time:

    sudo journalctl -u devcontrol-web.service -f

# Run DevControl

To run DevControl prepare your configuration in **`bin/devcontrol/devcontrol.yml`** (see the example file)

Having the backend and web services both running (see above), then navigate to **`http://your_server_ip:8081`**

# Troubleshooting

If you need to monitor and debug the backend:

- stop the backend service
- run it in a terminal in vervose mode: `python3 bin/devcontrol_srv.py -v`

Example:
    
    shome@rpi3clac:~ $ python3 bin/devcontrol_srv.py -v
    (devcontrol.py) logging commands in '/home/shome/bin/devcontrol/modules/../devcontrol.log'
    (devcontrol.py) threading loop for refreshing the status in background ...'
    (devcontrol) will run 'devcontrol' module at 0.0.0.0:9950 ...
    (devcontrol) Rx: hello
    (devcontrol) Tx: hi!




