# A wake-on-lan web

If you have a 24x7 Raspberry Pi kind of Linux based micro PC running at home, you may want to use it as a WOL server to power on some local machines.

On your 24x7 micro PC you'll need:

- `sudo apt install wakeonlan`

- Enable the optional apache site configuration:

        sudo a2ensite   wol.conf
        sudo service apache2 reload

- Configure the MAC address of your devices

        nano wolservice/wolservice.cfg

- Autorun the server, for example inside /etc/rc.local

    su -l ME -c "python3 /home/ME/bin/wolserver.py" &


Then, simply bookmark `http://microPC_IP:8081` on your favourite smartphone or tablet web browser.

<a href="url"><img src="bin/wolserver/img/WakeOnLAN_web.png" align="center" width="480" ></a>
