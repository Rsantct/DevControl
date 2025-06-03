<?php

    /*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
    */

    $UHOME = get_home();
    $CFGPATH = $UHOME."/bin/devcontrol/devcontrol.yml";

    // echo "UHOME: ".$UHOME."\n"; // cmdline debugging

    // Gets the HOME folder assuming this php code is placed under ~/bin/
    function get_home() {
        $phpdir = getcwd();
        $pos = strpos($phpdir, 'bin/devcontrol');
        $uhome= substr($phpdir, 0, $pos-1);
        return $uhome;
    }


    // Reads an item's value from the 'devcontrol.yml' YAML file
    function get_config($item) {

        global $UHOME;
        global $CFGPATH;

        $config = yaml_parse_file($CFGPATH);

        return $config[$item];
    }


    // Communicates to the pe.audio.sys TCP server.
    function system_socket ($cmd) {

        $address =         get_config( "server_addr" );
        $port    = intval( get_config( "server_port" ) );

        // Creates a TCP socket
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            echo "socket_create() failed: " . socket_strerror(socket_last_error()) . "\n";
            return '';
        }

        socket_set_option($socket, SOL_SOCKET, SO_RCVTIMEO, array("sec"=>0, "usec"=>500));
        socket_set_option($socket, SOL_SOCKET, SO_SNDTIMEO, array("sec"=>0, "usec"=>500));

        $so_result = socket_connect($socket, $address, $port);
        if ($so_result === false) {
            echo "(comms.php) socket_connect() failed: ($so_result) " . socket_strerror(socket_last_error($socket)) . "\n";
            return '';
        }

        // PHP ---> App server side
        socket_write($socket, $cmd, strlen($cmd));

        // App server side ---> PHP
        $ans = '';
        while ( ($tmp = socket_read($socket, 1000)) !== '') {
           $ans = $ans.$tmp;
        }
        socket_close($socket);

        return $ans;
    }

?>
