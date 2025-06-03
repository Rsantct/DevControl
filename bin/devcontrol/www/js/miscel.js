/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/


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

        //console.log('envia_com respuTxt:', respuTxt);
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


export function btn_color(btn, onoff){

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
