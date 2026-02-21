/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/


// Check if `x` is a non void object, e.g. a dictionary
export function isPlainObject(x) {
  return Object.prototype.toString.call(x) === '[object Object]';
}


export async function send_cmd(cmd) {
    // Si la petición tarda más de 4 segundos, la cancelamos
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    try {
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) throw new Error('backend error');

        const respuTxt = await response.text();

        try {
            return JSON.parse(respuTxt.replaceAll(': null', ': ""'));

        } catch {
            if (respuTxt.toLowerCase().includes('refused')){
                return 'server error'
            }else{
                return respuTxt;
            }
        }

    } catch (err) {
        // Differ on timeout or network error
        if (err.name === 'AbortError') {
            return 'server timeout';
        }
        return JSON.stringify({ error: true, reason: err.message });
    }
}


export async function try_connection() {
    const tmp = await send_cmd('hello');
    if (tmp == 'hi!') {
        return true
    }else{
        return false
    }
}


export function display_warning_and_hide_sections(yes=false, isTimeout=false){

    const warningDiv = document.getElementById("div_warnings");
    const sections = ["div_wol", "div_plugs", "div_scripts", "div_zigbees"];

    if (yes){

        warningDiv.style.display = 'block';
        sections.forEach(id => document.getElementById(id).style.display = 'none');

        warningDiv.className = 'warning_box_error';

        if (isTimeout) {
            warningDiv.classList.add('warning_timeout');
            warningDiv.innerHTML = `⚠️ <b>Timeout:</b> time out ...`;

        } else {
            warningDiv.innerHTML = `❌ <b>Error:</b> no response from backend`;
        }

    }else{

        warningDiv.style.display = 'none';
        sections.forEach(id => document.getElementById(id).style.display = 'block');
    }
}


export function btn_color(btn, onoff=null){
    // `onoff` values:
    //          'on'    -->     green
    //          'off'   -->     red
    //          other   -->     gray


    if ( onoff == 'on') {
        btn.style = 'initial';
        btn.style.borderColor = 'green';

    }else if (onoff == 'off') {
        btn.style = 'initial';
        btn.style.borderColor = 'darkred';

    }else{
        btn.style.borderColor = 'darkgray';
        btn.style.color = 'darkgray';
    }
}


export async function make_section(div_id, section_title, section_items, btn_handler){

    if ( ! section_items || ! isPlainObject(section_items) ){
        console.error(`Error: ${section_title} not a valid objet:`, section_items);
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

        // display Zigbees schedule
        if ( div_id == 'div_zigbees' ){

            const schedules = section_items[item].schedule;

            const sched_str = sched_dict_2_string( schedules );

            info_cell.innerHTML = sched_str;

        }

        // display plug device schedule
        if (div_id == 'div_plugs'){

            const schedules = await send_cmd( 'plug {"target": "' + item + '", "command": "schedule", "schedule": "nice_list"}' );

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

function sched_dict_2_string( d ){

    //  d = {
    //      "switch_off": "00  11  02   * * *",
    //      "switch_on": ""                     // this will be discarded
    //  }

    // Convert to array and  filer empty values
    const resultados = Object.entries(d)
      .filter(([_, val]) => val.trim() !== "") // discarded if empty
      .map(([key, cronValue]) => {

        const parts = cronValue.trim().split(/\s+/);
        const action = key.split('_')[1].toUpperCase();

        // Logic for 6 parts (sec min hour ...) or 5 parts (min hour ...)
        let timeStr, remaining;

        if (parts.length >= 6) {
          // 00(sec) 11(min) 02(hour) -> 02:11
          timeStr = `${parts[2]}:${parts[1]}`;
          remaining = parts.slice(3).join(" ");
        } else {
          // 11(min) 02(hour) -> 02:11
          timeStr = `${parts[1]}:${parts[0]}`;
          remaining = parts.slice(2).join(" ");
        }

        return `${action}: ${timeStr} ${remaining}`;
      });

    let txt = '';
    resultados.forEach(res => {
        txt += res + '\n';
    });

    return txt;
}
