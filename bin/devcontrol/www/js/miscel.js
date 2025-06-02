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
