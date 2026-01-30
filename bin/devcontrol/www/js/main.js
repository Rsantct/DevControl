/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/

import * as mc from "./miscel.js";

// seconds
var REFRESH_INTERVAL = 5;

// Object to keep the different wol info cells until waiting counter expired,
// while waiting for PC to be `up` after sending a WOL packet
var WOL_REFRESH_COUNT = {};
// Seconds to keep `waiting for response` after sending a WOL packet
const WAIT_4_WOL = 30;

var STATUS = {};

// WOL PCs
function do_wol(event){

    if ( ! confirm('Please CONFIRM to send WOL packet') ){
            return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const wol_id = btn.id.slice(3,);

    const ans = mc.send_cmd( 'wol {"target": "' + wol_id + '", "command":"send"}' );

    // Highlights the button for a second
    btn.className = 'ctrl_button_highlighted';
    setTimeout(function(){
            btn.className = 'ctrl_button';
        }, 1000);

    if ( ans.toLowerCase().includes('sending') ){
        const info_cell = document.getElementById('info_' + wol_id);
        info_cell.innerHTML = 'waiting for ping response ...';
        WOL_REFRESH_COUNT[wol_id] = WAIT_4_WOL;
    }

}


function fill_in_wol_buttons(wol_devices) {

    mc.make_section('div_wol', 'Wake On LAN PCs', devices.wol, do_wol);

    // initializes the counter for all WOL devices
    for (const wol_id in devices.wol){
        WOL_REFRESH_COUNT[wol_id] = 0;
    }
}


function wol_refresh(){

    for (const wol_id in devices.wol) {

        const btn = document.getElementById('bt_' + wol_id);

        const ping = STATUS.wol[wol_id];

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
function do_plug_toggle(event){

    const btn = event.target;

    // example 'bt_Plug_01'
    const plug_id = btn.id.slice(3,);

    // confirm switching
    if ( btn.style.color != 'darkgrey' ) {

        if ( ! confirm('Please CONFIRM to switch') ){
                return;
        }

    }else{

        alert('The plug is NOT responding');
        return;
    }

    const ans = mc.send_cmd( 'plug {"target": "' + plug_id + '", "command": "toggle"}' );


    // Highlights the button for a second
    btn.className = 'ctrl_button_highlighted';
    setTimeout(function(){
            btn.className = 'ctrl_button';
        }, 1000);

    if (ans == 'on'){
        btn.style.borderColor = 'green';
    }else{
        btn.style.borderColor = 'darkred';
    }
}


function fill_in_plug_buttons(plugs) {
    mc.make_section('div_plugs', 'Smart Plugs', devices.plugs, do_plug_toggle);
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
function do_script(event){

    if ( ! confirm('Please CONFIRM to RUN the script') ){
        return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const script_id = btn.id.slice(3,);

    const response = mc.send_cmd( 'script {"target": "' + script_id + '", "command": "run"}' );
    alert('response was: ' + response);

    // Display current status
    mc.btn_color(btn, response);
}


function fill_in_scripts_buttons(scripts) {
    mc.make_section('div_scripts', 'Scripts', scripts, do_script);
}


function scripts_refresh(){

    for (const script_id in scripts) {

        const btn = document.getElementById('bt_' + script_id);

        // Button color
        const onoff = STATUS.scripts[script_id];
        mc.btn_color(btn, onoff);
    }
}


// ZIGBEES
function do_zigbee(event){

    if ( ! confirm('Please CONFIRM to TOGGLE') ){
        return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const zigbee_id = btn.id.slice(3,);

    const response = mc.send_cmd( 'zigbee {"target": "' + zigbee_id + '", "command": "toggle"}' );
    alert('response was: ' + response);

    // Display current status
    mc.btn_color(btn, response);
}


function fill_in_zigbee_buttons(zigbees) {
    mc.make_section('div_zigbees', 'Zigbee devives', zigbees, do_zigbee);
}


function zigbees_refresh(){

    for (const z_id in zigbees) {

        const btn = document.getElementById('bt_' + z_id);

        // Button color
        const onoff = STATUS.zigbees[z_id];
        mc.btn_color(btn, onoff);
    }
}


// MAIN

function do_refresh() {

    if ( mc.try_connection() ) {

        STATUS = mc.send_cmd( 'get_status' );

        if ( mc.isPlainObject(STATUS) ) {
            wol_refresh();
            plugs_refresh();
            scripts_refresh();
            zigbees_refresh();
        }
    }
}


if ( mc.try_connection() ) {

    var devices = mc.send_cmd( 'get_config {"section": "devices"}' );
    var scripts = mc.send_cmd( 'get_config {"section": "scripts"}' );
    var zigbees = mc.send_cmd( 'get_config {"section": "zigbees"}' );

    fill_in_wol_buttons(devices.wol);
    fill_in_plug_buttons(devices.plugs);
    fill_in_scripts_buttons(scripts);
    fill_in_zigbee_buttons(zigbees);

    // PAGE REFRESH

    const refresh_config = mc.send_cmd( 'get_config {"section": "refresh"}' );

    if (refresh_config.web_refresh_interval) {
        REFRESH_INTERVAL = refresh_config.web_refresh_interval;
    }

    do_refresh();
    setInterval( do_refresh, REFRESH_INTERVAL * 1000);
}
