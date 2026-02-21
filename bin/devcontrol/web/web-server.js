/*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
*/

const express = require('express');
const net = require('net');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const os = require('os');

const app = express();
const PORT_WEB = 8081;
const BACKEND_TIMEOUT = 500

const CONFIG_PATH = path.join(os.homedir(), 'bin/devcontrol/devcontrol.yml');


// Command line option '-v' VERBOSE
let verbose     = false;
process.argv.slice(2).forEach(opt => {
    if (opt === '-v') {
        verbose = true;
        console.log('(verbose mode)')
    }
});


function getConfig() {
    try {
        const fileContents = fs.readFileSync(CONFIG_PATH, 'utf8');
        return yaml.load(fileContents);
    } catch (e) {
        console.error("Error reading YAML:", e);
        return null;
    }
}

// tcp bridge (promised to use async/await)
function systemSocket(cmd) {
    return new Promise((resolve, reject) => {
        const config = getConfig();
        if (!config) return reject("Cannot load config");

        const client = new net.Socket();
        let response = '';

        client.setTimeout(BACKEND_TIMEOUT);

        client.connect(config.server_port, config.server_addr, () => {
            client.write(cmd);
        });

        client.on('data', (data) => {
            response += data.toString();
        });

        client.on('end', () => resolve(response));

        client.on('error', (err) => reject(err.message));

        client.on('timeout', () => {
            client.destroy();
            // we return whatever we have up to the timeout
            resolve(response);
        });
    });
}

// Static files are found in the 'public/' folder
app.use(express.static('public'));
// we need json to listen commands in API RESTful style
app.use(express.json());

// API RESTful style
app.post('/api/command', async (req, res) => {

    const { command } = req.body;

    if (!command) {
        return res.status(400).json({ error: "No command found" });
    }

    try {
        const result = await systemSocket(command);
        if (verbose) {
            console.log('Rx:',  command);
            console.log('Tx:',  result);
        }

        // if backend is JSON, try to return JSON to frontend
        try {
            res.json(JSON.parse(result));
        // else plain text
        } catch {
            res.send(result);
        }
    } catch (error) {
        res.status(500).json({ error: "Backend error", detail: error });
    }
});


app.listen(PORT_WEB, () => {
    console.log(`Node.js server active at port ${PORT_WEB}`);
    console.log(`Reading config at: ${CONFIG_PATH}`);
});
