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

    var table = document.getElementById("main_wol_table");

    for (const device in wol_devices) {

        var row = table.insertRow();
        var cell = row.insertCell();
        cell.className = 'device_cell';

        var btn = document.createElement('button');
        btn.type = "button";
        btn.className = "device_button";
        // example 'bt_Amplifier'
        btn.id = 'bt_' + device;
        btn.innerHTML = device;
        btn.addEventListener('click', do_wol);

        cell.appendChild(btn);
    }
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

    var table = document.getElementById("main_plugs_table");

    for (const plug in plugs) {

        var row = table.insertRow();
        var cell = row.insertCell();
        cell.className = 'device_cell';

        var btn = document.createElement('button');
        btn.type = "button";
        btn.className = "device_button";
        // example 'bt_Plug_01'
        btn.id = 'bt_' + plug;
        btn.innerHTML = plug;
        btn.addEventListener('click', do_plug_toggle);

        cell.appendChild(btn);

        // Display current status
        const onoff = mc.send_cmd( 'plug {"target": "' + plug + '", "mode": "status"}' );
        mc.btn_color(btn, onoff);
    }
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
// (i) There is no refresh here, we just display the result
//     for 1 second when running the script.
function do_script(event){

    if ( ! confirm('Please CONFIRM to RUN the script') ){
            return;
    }

    const btn = event.target;

    // example 'bt_Amplifier'
    const script_id = btn.id.slice(3,);

    const response = mc.send_cmd( 'script {"target": "' + script_id + '"}' );
    alert('response was: ' + response);

    // (i) Dot notation does not works when the key having spaces
    const expected_response = scripts[script_id].response;
    if ( response == expected_response ) {
        mc.btn_color(btn, 'on');
        setTimeout( () => {
            btn.style = "initial";
        } , 1000);
    }
}


function fill_in_scripts_buttons(scripts) {

    var table = document.getElementById("main_scripts_table");

    for (const script in scripts) {

        var row = table.insertRow();
        var cell = row.insertCell();
        cell.className = 'device_cell';

        var btn = document.createElement('button');
        btn.type = "button";
        btn.className = "device_button";
        // example 'Amplifier'
        btn.id = 'bt_' + script;
        btn.innerHTML = script;
        btn.addEventListener('click', do_script);

        cell.appendChild(btn);
    }
}


// MAIN

function do_refresh() {

    if ( mc.try_connection() ) {

        wol_refresh()
        plugs_refresh()
    }
}


if ( mc.try_connection() ) {

    var devices = mc.send_cmd( 'get_config {"section": "devices"}' );
    var scripts = mc.send_cmd( 'get_config {"section": "scripts"}' );

    fill_in_wol_buttons(devices.wol);

    fill_in_plug_buttons(devices.plugs);

    fill_in_scripts_buttons(scripts);

    // PAGE REFRESH
    const web_config = mc.send_cmd( 'get_config {"section": "web_config"}' );
    if (web_config.refresh_seconds) {
        REFRESH_INTERVAL = web_config.refresh_seconds * 1000
    }

    setInterval( do_refresh, REFRESH_INTERVAL );
}
