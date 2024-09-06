#!/bin/bash

# To run the application:
# 0. Run 'make' to build docker container(s) (if they are not already built);
# 1. Prepare env file(s): check ./local_env/private.env.example.
# 2. Run './run_local.sh' to start docker containers;
# Execute permissions should be given to run_local.sh file beforehand
# ('chmod +x ./run_local.sh').
# Application will run on port 8080 - it has to be free.

echo "Press [CTRL+C] to stop.."

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

function ctrl_c() {
    echo "** Trapped CTRL-C"
    exit 0
}

docker run -t --net=host \
       -e "PORT=8080" \
       --env-file ./local_env/public.env \
       --env-file ./local_env/private.env \
       zenkraft-test-main:latest

while true
do
    sleep 1
done
