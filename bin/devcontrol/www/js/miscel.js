/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/


// Check if `x` is a non void object, e.g. a dictionary
export function isPlainObject(x) {
  return Object.prototype.toString.call(x) === '[object Object]';
}


export function send_cmd( cmd ) {

    cmd = encodeURIComponent(cmd);
    const url = '/php/main.php?command=' + cmd;

    const miPET = new XMLHttpRequest();
    let respuTxt = '';

    try {                    // ASYNC
        miPET.open("POST", url, false);
        miPET.send();
        respuTxt = miPET.responseText;
    }
    catch(err) {
        respuTxt = JSON.stringify( {"autorizado": false, "razon": err.message} );
    }


    // JSON ANSWER
    try{
        const respuJson = JSON.parse(respuTxt.replaceAll(': null', ': ""'));
        //console.log('envia_com respuJson:', respuJson);
        return respuJson

    // TEXT ANSWER
    }catch{

        if( respuTxt.toLowerCase().includes('connection refused') ){
            respuTxt = 'server connection error';
        }

        // alert(respuTxt);
        return respuTxt;
    }
}


export function try_connection() {

    let res = false

    const tmp = send_cmd( 'hello' );

    if ( typeof tmp == 'string' && tmp.includes('connection error') ) {

        document.getElementById("div_wol").style.display     = 'none';
        document.getElementById("div_plugs").style.display   = 'none';
        document.getElementById("div_scripts").style.display = 'none';

        document.getElementById("div_warnings").style.display = 'block';
        document.getElementById("div_warnings").innerHTML = tmp;

    }else{

        document.getElementById("div_wol").style.display     = 'block';
        document.getElementById("div_plugs").style.display   = 'block';
        document.getElementById("div_scripts").style.display = 'block';

        document.getElementById("div_warnings").style.display = 'none';
        document.getElementById("div_warnings").innerHTML = '';

        res = true
    }

    return res
}


export function btn_color(btn, onoff=null){
    // `onoff` values:
    //          'on'    -->     green
    //          'off'   -->     red
    //          other   -->     grey


    if ( onoff == 'on') {
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


export function make_section(div_id, section_title, section_items, btn_handler){

    if ( ! section_items ){
        return;
    }

    let table   = document.createElement("table");
    table.id = div_id.replace('div', 'table');

    let theader = table.createTHead();
    let tbody   = table.createTBody();
    let hrow    = theader.insertRow();
    let h_title_cell = hrow.insertCell();
    let h_info_cell  = hrow.insertCell();

    h_title_cell.innerHTML = section_title;
    h_info_cell.innerHTML = ''

    for (const item in section_items) {

        let row = tbody.insertRow();

        let butn_cell = row.insertCell();
        butn_cell.className = 'device_cell';

        let info_cell = row.insertCell();
        info_cell.className = 'info_cell';
        info_cell.id = 'info_' + item;

        let btn = document.createElement('button');
        btn.type = "button";
        btn.className = "ctrl_button";
        // example 'bt_Amplifier'
        btn.id = 'bt_' + item;
        btn.innerHTML = item;
        btn.addEventListener('click', btn_handler);

        butn_cell.appendChild(btn);

        if (div_id == 'div_plugs'){

            // display plug device schedule
            const schedules = send_cmd( 'plug {"target": "' + item + '", "mode": "schedule", "schedule": "nice_list"}' );

            if ( Array.isArray(schedules) ){

                for (const s of schedules) {
                    info_cell.innerHTML += s[1].padEnd(3, ' ').replace(' ', '&nbsp;') + ' ' + s[0] + '<br>';
                }

            }else{
                info_cell.innerHTML += '--'
            }
        }
    }

    document.getElementById(div_id).appendChild(table)
}


