#!/bin/bash

############################################################
# PROGRAMAR EN CRONTAB, ejemplo:
#   # Qnas monitor cada 20 minutos
#   */20 * * * * $HOME/bin/qnas_get_status.sh
############################################################

nas_host='qnas.local'
nas_user='admin'
# sin passwdord, acceso preparado con ssh-copy-id

# Archivos de respuesta
mkdir -p $HOME/bin/qnas
logpath=$HOME/bin/qnas/state.log
errpath=$HOME/bin/qnas/state.err

# comandos
q_cpu_temp='echo "$(($(cat /sys/class/thermal/thermal_zone0/temp)/1000)) °C"'
q_hdd_temp='getsysinfo hdtmp 1'
# OjO esto no es un reflejo real de 'standby'
q_hdd_status='cat /sys/block/sda/device/power/runtime_status'

# cadena de comandos
q_all="$q_cpu_temp"" && ""$q_hdd_temp"" && ""$q_hdd_status"

# respuesta
# -o BatchMode=yes evita que el comando se quede colgado esperando una interacción si la conexión falla
ans=$(/usr/bin/ssh -i $HOME/.ssh/id_ed25519 \
    -o BatchMode=yes \
    -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=no \
    "$nas_user"@"$nas_host" "$q_all" 2>$errpath
)

# DEBUG
# echo $ans

# La respuesta es algo así como '58 °C 36 C/96 Factive', sin LF al final, donde
#   cpu_temp   = 58 °C
#   hdd_temp   = 36 °C / 96 °F
#   hdd_status = active

# Buscamos secuencias de dígitos para las temperaturas
if [[ $ans =~ ([0-9]+)\ [^0-9]+([0-9]+) ]]; then
    cpu_temp=${BASH_REMATCH[1]}
    hdd_temp=${BASH_REMATCH[2]}
else
    exit 0
fi

# (obsoleto) El estado del HDD viene al final
hdd_state="${ans##* }"      # 'Factive'
hdd_state="${hdd_state:1}"  # quita la primera letra que viene pegada de lo anterior

# Timestamp en formato ISO
timestamp=$(date +%Y-%m-%dT%H:%M:%S)

# hacemos un json por línea en el archivo de respuestas
json='{"cpu_temp": '$cpu_temp', "hdd_temp": '$hdd_temp', "time": "'$timestamp'"}'
echo $json
echo $json >> $logpath
