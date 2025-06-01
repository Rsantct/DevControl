<?php

    /*
    Copyright (c) Rafael Sánchez
    This file is part of 'DevControl'
    a very simple Home Automation app.
    */

    include 'comms.php';

    $command = $_REQUEST["command"];
    echo system_socket( $command );

?>
