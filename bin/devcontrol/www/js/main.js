/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/

import * as mc from "./miscel.js";

const REFRESH_INTERVAL = 3000;

// WOL PCs

function do_wol(event){

    const btn = event.target;

    // example 'bt_Amplifier'
    const wol_id = btn.id.slice(3,);

    mc.send_cmd( 'wol {"target": "' + wol_id + '"}' );

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


// PLUGS

function do_plug_toggle(event){

    const btn = event.target;

    // example 'bt_Plug_01'
    const plug_id = btn.id.slice(3,);

    // confirm switching
    //if ( btn.style.borderColor == 'green' ) {
    if ( ! confirm('Please CONFIRM to switch') ){
            return
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

        if (onoff == 'on'){
            btn.style.borderColor = 'green';
        }else{
            btn.style.borderColor = 'darkred';
        }
    }
}


function plugs_refresh(){

    for (const plug in devices.plugs) {

        const btn = document.getElementById('bt_' + plug);

        // Display current status
        const onoff = mc.send_cmd( 'plug {"target": "' + plug + '", "mode": "status"}' );

        //console.log(plug, onoff)

        if ( onoff == 'on' ) {
            btn.style = 'initial';
            btn.style.borderColor = 'green';

        }else if (onoff == 'off') {
            btn.style = 'initial';
            btn.style.borderColor = 'darkred';

        }else{
            btn.style.borderColor = 'darkgrey';
            btn.style.color = 'darkgrey';
        }
    }
}


// SCRIPTS

function do_script(event){

    const btn = event.target;

    // example 'bt_Amplifier'
    const script_id = btn.id.slice(3,);

    mc.send_cmd( 'script {"target": "' + script_id + '"}' );

    // Highlights the button for a second
    btn.className = 'device_button_highlighted';
    setTimeout(function(){
            btn.className = 'device_button';
        }, 1000);
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

function try_connection() {

    let res = false

    const tmp = mc.send_cmd( 'hello' );

    if ( typeof tmp == 'string' && tmp.includes('connection error') ) {

        document.getElementById("div_wol").style.display     = 'none';
        document.getElementById("div_plugs").style.display   = 'none';
        document.getElementById("div_scripts").style.display = 'none';

        document.getElementById("warnings").style.display = 'block';
        document.getElementById("warnings").innerHTML = tmp;

    }else{

        document.getElementById("div_wol").style.display     = 'block';
        document.getElementById("div_plugs").style.display   = 'block';
        document.getElementById("div_scripts").style.display = 'block';

        document.getElementById("warnings").style.display = 'none';
        document.getElementById("warnings").innerHTML = '';

        res = true
    }

    return res
}


// Currently only plugs have refresh
function do_refresh() {

    if ( try_connection() ) {

        plugs_refresh()
    }
}


if ( try_connection() ) {

    var devices = mc.send_cmd( 'get_config {"section": "devices"}' );
    var scripts = mc.send_cmd( 'get_config {"section": "scripts"}' );


    fill_in_wol_buttons(devices.wol);

    fill_in_plug_buttons(devices.plugs);

    fill_in_scripts_buttons(scripts);

    // PAGE REFRESH
    setInterval( do_refresh, REFRESH_INTERVAL );
}
