# Shelly Plus Plug S

https://kb.shelly.cloud/knowledge-base/shelly-plus-plug-s-user-and-safety-guide

The LED indication ring (A) will start flashing with a blue light, indicating the Device is in Access Point (AP) mode. You can access the embedded web interface at
http://192.168.33.1
in the Wi‑Fi network, created by the Device (ShellyPlusPlugS-XXXXXXXXXXXX) and use it to control the Device and change its settings.
You can now plug an appliance into the Device socket (B).


## http commands

    | Acción    |  Comando HTTP Shelly Plus       |
    | --------- | ------------------------------- |
    | Consultar |  /rpc/Switch.GetStatus?id=0     |
    | Encender  |  /rpc/Switch.Set?id=0&on=true   |
    | Apagar    |  /rpc/Switch.Set?id=0&on=false  |
    | Alternar  |  /rpc/Switch.Toggle?id=0        |



OjO es más rápido con la IP que con el nombre .local

OjO opcion con autenticacion hay que poner --digest o --anyauth

curl --digest -u admin:xxxxxxxx "http://192.168.1.58/rpc/Switch.GetStatus?id=0"


