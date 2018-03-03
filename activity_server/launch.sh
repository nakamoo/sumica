#!/bin/bash

parallel()
{
    for cmd in "$@"; do {
      echo "Process \"$cmd\" started";
      $cmd & pid=$!
      PID_LIST+=" $pid";
    } done

    trap "kill $PID_LIST" SIGINT

    echo "Parallel processes have started";

    wait $PID_LIST

    echo
    echo "All processes have completed";
}

parallel "python3 action_server.py" "python3 pose_server.py" "python3 object_server.py"