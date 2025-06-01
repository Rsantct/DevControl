/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/

import * as mc from "./miscel.js";


// WOL PCs

function do_wol(event){

    const btn = event.target;

    // example 'bt_Amplifier'
    const wol_id = btn.id.slice(3,);

    mc.send_cmd('wol ' + wol_id);

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

    const ans = mc.send_cmd('plug ' + plug_id + ' toggle');

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
        const onoff = mc.send_cmd('plug ' + plug + ' status');
        if (onoff == 'on'){
            btn.style.borderColor = 'green';
        }else{
            btn.style.borderColor = 'darkred';
        }
    }
}


// MAIN

const devices = mc.send_cmd('get_devices');

fill_in_wol_buttons(devices.wol);

fill_in_plug_buttons(devices.plugs);
