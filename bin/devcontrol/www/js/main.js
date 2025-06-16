/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/

import * as mc from "./miscel.js";

var REFRESH_INTERVAL = 5000;


// WOL PCs

function do_wol(event){

    if ( ! confirm('Please CONFIRM to send WOL packet') ){
            return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const wol_id = btn.id.slice(3,);

    mc.send_cmd( 'wol {"target": "' + wol_id + '", "mode":"send"}' );

    // Highlights the button for a second
    btn.className = 'device_button_highlighted';
    setTimeout(function(){
            btn.className = 'device_button';
        }, 1000);
}


function fill_in_wol_buttons(wol_devices) {

    mc.make_section('div_wol', 'Wake On LAN PCs', devices.wol, do_wol);
}


function wol_refresh(){

    for (const wol in devices.wol) {

        const btn = document.getElementById('bt_' + wol);

        // Display current status
        const ping = mc.send_cmd( 'wol {"target": "' + wol + '", "mode": "ping"}' );

        let onoff = "off"

        if ( ping.includes('on') || ping.includes('up') || ping == '1'  ){
            onoff = "on"
        }

        mc.btn_color(btn, onoff);
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

    const ans = mc.send_cmd( 'plug {"target": "' + plug_id + '", "mode": "toggle"}' );


    // Highlights the button for a second
    btn.className = 'device_button_highlighted';
    setTimeout(function(){
            btn.className = 'device_button';
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

    for (const plug in devices.plugs) {

        const btn = document.getElementById('bt_' + plug);

        // Display current status
        const onoff = mc.send_cmd( 'plug {"target": "' + plug + '", "mode": "status"}' );
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

    const response = mc.send_cmd( 'script {"target": "' + script_id + '", "mode": "run"}' );
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

        // Display current status
        const onoff = mc.send_cmd( 'script {"target": "' + script_id + '", "mode": "status"}' );
        mc.btn_color(btn, onoff);
    }
}


// MAIN

function do_refresh() {

    if ( mc.try_connection() ) {

        wol_refresh();
        plugs_refresh();
        scripts_refresh();
    }
}


if ( mc.try_connection() ) {

    var devices = mc.send_cmd( 'get_config {"section": "devices"}' );
    var scripts = mc.send_cmd( 'get_config {"section": "scripts"}' );

    fill_in_wol_buttons(devices.wol);

    fill_in_plug_buttons(devices.plugs);

    fill_in_scripts_buttons(scripts);

    // PAGE REFRESH
    do_refresh();
    const web_config = mc.send_cmd( 'get_config {"section": "web_config"}' );
    if (web_config.refresh_seconds) {
        REFRESH_INTERVAL = web_config.refresh_seconds * 1000
    }

    setInterval( do_refresh, REFRESH_INTERVAL );
}
