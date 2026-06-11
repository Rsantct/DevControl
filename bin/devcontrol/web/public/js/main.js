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

var STATUS     = {};
var DEVICES    = {};
var SCRIPTS    = {};
var ST_DAEMONS = {};
var UI_INITIALIZED = false;


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
    // Usamos wol_devices (el parámetro), no la variable global DEVICES

    const title = 'Wake On LAN PCs';
    // Leave the title blank
    await mc.make_section('div_wol', '', wol_devices, do_wol);

    for (const wol_id in wol_devices){
        WOL_REFRESH_COUNT[wol_id] = 0;
    }
}


function wol_refresh(){

    for (const wol_id in DEVICES.wol) {

        const btn = document.getElementById('bt_' + wol_id);

        const ping = STATUS.wol[wol_id]["state"];

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
    const title = 'Smart Plugs';
    // Leave the title blank
    await mc.make_section('div_plugs', '', plugs_data, do_plug_toggle);
}


function plugs_refresh(){

    for (const plug_id in DEVICES.plugs) {

        const btn = document.getElementById('bt_' + plug_id);

        // Button color
        const onoff = STATUS.plugs[plug_id]["state"];
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
    const title = 'Scripts';
    // Leave the title blank
    await mc.make_section('div_scripts', '', scripts_data, do_script);
}


function scripts_refresh(){

    for (const script_id in SCRIPTS) {

        const btn = document.getElementById('bt_' + script_id);

        // Button color
        const onoff = STATUS.scripts[script_id]["state"];

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
    const title = 'Zigbee lights';
    // Leave the title blank
    await mc.make_section('div_zigbees', '', zigbees_data, do_zigbee);
}


function zigbees_refresh(){

    for (const z_id in DEVICES.zigbees) {

        const btn = document.getElementById('bt_' + z_id);

        // Button color
        const onoff = STATUS.zigbees[z_id]["state"];

        if (!onoff){
            continue
        }

        mc.btn_color(btn, onoff);

        // Info cell
        const timer = STATUS.zigbees[z_id]['timer'];
        if (timer){
            document.getElementById('info_' + z_id).innerHTML += '<br>' + timer;
        }
    }
}


// STATUS DAEMONS
async function fill_in_st_daemons_buttons(st_daemons_data) {

    const title = 'Other devices';
    // Leave the title blank
    await mc.make_section('div_status_daemons', '', st_daemons_data, null);
}


function st_daemons_refresh(){

    for (const sd_id in ST_DAEMONS) {

        const btn = document.getElementById('bt_' + sd_id);

        let outdated_seconds = ST_DAEMONS[sd_id]["outdated_seconds"]
        if ( ! outdated_seconds ) {
            outdated_seconds = 60;
        }

        const alerts = ST_DAEMONS[sd_id]["alerts"];

        const st = STATUS["status_daemons"][sd_id]["state"];
        // Example:
        // "QNAP TS-228"
        // {cpu_temp: 61, hdd_temp: 42, hdd_state: "active", time: "20260521T221502"}

        if (!st){
            continue
        }

        document.getElementById('info_' + sd_id).innerHTML = '';

        const outdated = mc.older_than( st.time, outdated_seconds);
        if (outdated) {
            document.getElementById('info_' + sd_id).innerHTML = '--';
            mc.btn_color(btn, 'gray');
            console.log(sd_id, 'OUTDATED timestamp', st.time);
            return
        }

        let alert = false;

        for (const [key, value] of Object.entries(st)) {

            if (key=='time'){
                continue
            }

            document.getElementById('info_' + sd_id).innerHTML += key + ': ' + value;

            if ( alerts[key].max !== null && value >= alerts[key].max){
                document.getElementById('info_' + sd_id).innerHTML += ' (max: ' + alerts[key].max + ')';
                console.log(key, value, 'max alert')
                alert = true;
            }
            if ( alerts[key].min !== null && value >= alerts[key].min){
                document.getElementById('info_' + sd_id).innerHTML += ' (min: ' + alerts[key].min + ')';
                console.log(key, value, 'min alert')
                alert = true;
            }

            document.getElementById('info_' + sd_id).innerHTML += '<br>';
        }

        if (alert){
            mc.btn_color(btn, 'alert');
        }else{
            mc.btn_color(btn, 'green');
        }
    }
}


// MAIN REFRESH
async function do_refresh() {

    let warning_msg = '';

    if (await mc.try_connection()) {

        STATUS = await mc.send_cmd('get_status');
        //console.log('get_status:', STATUS);

        if ( mc.isPlainObject(STATUS) ) {

            if ( mc.older_than(STATUS.timestamp, 30) ) {
                warning_msg = 'received data is obsolete';
                mc.display_warning_and_hide_sections(true, warning_msg);

            }else{
                mc.display_warning_and_hide_sections(false);

                wol_refresh();
                plugs_refresh();
                scripts_refresh();
                zigbees_refresh();
                st_daemons_refresh();
            }

        }else{
            warning_msg = 'bad received data';
            mc.display_warning_and_hide_sections(true, warning_msg);
        }

    }else{
        warning_msg = 'no response from backend';
        mc.display_warning_and_hide_sections(true, warning_msg);
    }
}


// --- MAIN ---

async function startApp() {

    const isConnected = await mc.try_connection();
    if (! isConnected ) {
        const warning_msg = 'Server not detected. Retrying in 5 s ...';
        mc.display_warning_and_hide_sections(true, warning_msg);
        setTimeout(startApp, 5000); // w/o location.reload()
        return;
    }

    if (! UI_INITIALIZED) {
        const success = await setupSystem();
        if (!success) {
            setTimeout(startApp, 5000);
            return;
        }
    }

    startPolling();
}


async function setupSystem() {
    try {

        DEVICES     = await mc.send_cmd('get_config {"section": "devices"}');
        SCRIPTS     = await mc.send_cmd('get_config {"section": "scripts"}');
        ST_DAEMONS  = await mc.send_cmd('get_config {"section": "status_daemons"}');
        const conf  = await mc.send_cmd('get_config {"section": "refresh"}');

        if (!mc.isPlainObject(DEVICES) || !mc.isPlainObject(SCRIPTS)) {
            throw new Error("Bad config data");
        }

        REFRESH_INTERVAL = conf.polling_interval || 5;

        await fill_in_wol_buttons(DEVICES.wol);
        await fill_in_plug_buttons(DEVICES.plugs);
        await fill_in_zigbee_buttons(DEVICES.zigbees);
        await fill_in_scripts_buttons(SCRIPTS);
        await fill_in_st_daemons_buttons(ST_DAEMONS);

        UI_INITIALIZED = true;

        return true;

    } catch (error) {
        console.error("Error building the UI:", error);
        return false;
    }
}


function startPolling() {
    // Here we use an autoexec function so that the first refresh is inmediate
    (async function pulse() {
        await do_refresh();
        setTimeout(pulse, REFRESH_INTERVAL * 1000);
    })();
}

startApp();
