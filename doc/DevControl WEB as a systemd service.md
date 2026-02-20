
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


