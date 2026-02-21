/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/

import * as mc from "./miscel.js";

// Default page refresh in seconds
var REFRESH_INTERVAL = 5;

// Object to keep the different wol info cells until waiting counter expired,
// while waiting for PC to be `up` after sending a WOL packet
var WOL_REFRESH_COUNT = {};

// Seconds to keep `waiting for response` after sending a WOL packet
const WAIT_4_WOL = 30;

var STATUS = {};
var devices = {};
var scripts = {};
var show_warning = false

// Prompt message when switching on a Zigbee:
const zigbee_on_msg =`
Brightness:  1...10
    Leave blank for default brightness

Timer:
    -Ns\t  (N seconds)
    -Nm\t  (N minutes)
    -N \t  (N minutes)
    -Nh\t  (N hours)

You can enter one or both parameters, for example
for brighness 3 and timer 1/2 h:

    3  -0.5h`;

// WOL PCs
async function do_wol(event){

    if ( ! confirm('Please CONFIRM to send WOL packet') ){
            return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const wol_id = btn.id.slice(3,);

    const ans = await mc.send_cmd( 'wol {"target": "' + wol_id + '", "command":"send"}' );

    // Highlights the button for a second
    btn.className = 'ctrl_button_highlighted';
    setTimeout(function(){
            btn.className = 'ctrl_button';
        }, 1000);

    // Button to gray until refresh
    btn.style.borderColor = 'darkgray';

    if ( ans.toLowerCase().includes('sending') ){
        const info_cell = document.getElementById('info_' + wol_id);
        info_cell.innerHTML = 'waiting for ping response ...';
        WOL_REFRESH_COUNT[wol_id] = WAIT_4_WOL;
    }

}


async function fill_in_wol_buttons(wol_devices) {
    // Usamos wol_devices (el parámetro), no la variable global devices
    await mc.make_section('div_wol', 'Wake On LAN PCs', wol_devices, do_wol);

    for (const wol_id in wol_devices){
        WOL_REFRESH_COUNT[wol_id] = 0;
    }
}


function wol_refresh(){

    for (const wol_id in devices.wol) {

        const btn = document.getElementById('bt_' + wol_id);

        const ping = STATUS.wol[wol_id];

        if (!ping){
            continue;
        }

        const is_Up = ping.includes('on') || ping.includes('up') || ping == '1';

        // Button color
        let onoff = "off"
        if ( is_Up  ){
            onoff = "on"
        }
        mc.btn_color(btn, onoff);

        // Info cell
        //console.log(WOL_REFRESH_COUNT);
        if ( WOL_REFRESH_COUNT[wol_id] <= 0 || is_Up ){
            const info_cell = document.getElementById('info_' + wol_id);
            info_cell.innerHTML = ping;
            WOL_REFRESH_COUNT[wol_id] = 0;

        // Still `waiting for response` do not change info cell
        }else{
            WOL_REFRESH_COUNT[wol_id] -= ( WAIT_4_WOL / REFRESH_INTERVAL );
        }
    }
}

// PLUGS
async function do_plug_toggle(event){

    const btn = event.target;

    // example 'bt_Plug_01'
    const plug_id = btn.id.slice(3,);

    // confirm switching
    if ( btn.style.color != 'darkgray' ) {

        if ( ! confirm('Please CONFIRM to switch') ){
                return;
        }

    }else{

        alert('The plug is NOT responding');
        return;
    }

    const ans = await mc.send_cmd( 'plug {"target": "' + plug_id + '", "command": "toggle"}' );


    // Highlights the button for a while
    btn.className = 'ctrl_button_highlighted';
    setTimeout(function(){
            btn.className = 'ctrl_button';
        }, 4000);

    // Button to gray until refresh
    btn.style.borderColor = 'darkgray';
}


async function fill_in_plug_buttons(plugs_data) {
    await mc.make_section('div_plugs', 'Smart Plugs', plugs_data, do_plug_toggle);
}


function plugs_refresh(){

    for (const plug_id in devices.plugs) {

        const btn = document.getElementById('bt_' + plug_id);

        // Button color
        const onoff = STATUS.plugs[plug_id];
        mc.btn_color(btn, onoff);
    }
}


// SCRIPTS
async function do_script(event){

    if ( ! confirm('Please CONFIRM to RUN the script') ){
        return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const script_id = btn.id.slice(3,);

    const response = await mc.send_cmd( 'script {"target": "' + script_id + '", "command": "run"}' );
    //alert('response was: ' + response);

    // Button to gray until refresh
    btn.style.borderColor = 'darkgray';
}


async function fill_in_scripts_buttons(scripts_data) {
    await mc.make_section('div_scripts', 'Scripts', scripts_data, do_script);
}


function scripts_refresh(){

    for (const script_id in scripts) {

        const btn = document.getElementById('bt_' + script_id);

        // Button color
        const onoff = STATUS.scripts[script_id];

        if (!onoff){
            continue
        }

        mc.btn_color(btn, onoff);
    }
}


// ZIGBEES
async function do_zigbee(event){

    // example 'bt_Amplifier'
    const btn = event.target;
    const z_id = btn.id.slice(3,);

    if ( ! confirm('Please CONFIRM to TOGGLE') ){
        return;
    }

    let params = null;

    if ( STATUS.zigbees[z_id] == 'off' ){
        params = prompt(zigbee_on_msg);
    }

    let cmd = ''
    if (STATUS.zigbees[z_id] == 'off'){
        console.log('current state: off');
        cmd = `zigbee {"target": "${z_id}", "command": "on"}`
        if (params){
            cmd = `zigbee {"target": "${z_id}", "command": "on ${params}"}`
        }
    }else if (STATUS.zigbees[z_id] == 'on'){
        console.log('current state: on');
        cmd = `zigbee {"target": "${z_id}", "command": "off"}`
    }

    if (cmd){
        const response = await mc.send_cmd( cmd );
        console.log('response was: ' + response);
        // Button to gray until refresh
        btn.style.borderColor = 'darkgray';
    }
}


async function fill_in_zigbee_buttons(zigbees_data) {
    await mc.make_section('div_zigbees', 'Zigbee lights', zigbees_data, do_zigbee);
}


function zigbees_refresh(){

    for (const z_id in devices.zigbees) {

        const btn = document.getElementById('bt_' + z_id);

        // Button color
        const onoff = STATUS.zigbees[z_id];

        if (!onoff){
            continue
        }

        mc.btn_color(btn, onoff);

        // Info cell (PENDING)
        const timer = STATUS.zigbees[z_id]['timer'];
        if (timer){
            document.getElementById('info_' + z_id).innerHTML += '<br>' + timer;
        }
    }
}


async function do_refresh() {

    if (await mc.try_connection()) {

        if ( show_warning ){
            mc.display_warning_and_hide_sections(false);
        }
        show_warning = false;

        STATUS = await mc.send_cmd('get_status');

        //console.log('get_status:', STATUS);

        if (mc.isPlainObject(STATUS)) {
            wol_refresh();
            plugs_refresh();
            scripts_refresh();
            zigbees_refresh();
        }
    }else{
        show_warning = true;
    }

    if ( show_warning ){
        mc.display_warning_and_hide_sections(true);
    }
}


// --- MAIN ---
(async () => {

    if (await mc.try_connection()) {

        devices = await mc.send_cmd('get_config {"section": "devices"}');
        scripts = await mc.send_cmd('get_config {"section": "scripts"}');

        await fill_in_wol_buttons(devices.wol);
        await fill_in_plug_buttons(devices.plugs);
        await fill_in_zigbee_buttons(devices.zigbees);
        await fill_in_scripts_buttons(scripts);

        const conf_refresh = await mc.send_cmd('get_config {"section": "refresh"}');

        REFRESH_INTERVAL = conf_refresh.polling_interval || 5;

        async function pulse() {
            await do_refresh();
            // next pulse only when do_refresh ends (either successfull or timeout)
            setTimeout(pulse, REFRESH_INTERVAL * 1000);
        }

        pulse();

    } else {
        show_warning = true;
        mc.display_warning_and_hide_sections(true);
        // If try_connection fails 1st time, loop to reload every 5 s
        setTimeout(() => location.reload(), 5000);
    }
})();
