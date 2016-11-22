#!/bin/bash

log() {
  echo "$1"
}

find /root/preupgrade/hooks -path '*/postupgrade/run_hook' | while read path;
do
    log "hook-runner: starting: $path"
    pushd "${path%/*}" >/dev/null
        chmod +x run_hook
        ./run_hook; es=$?
        log "hook-runner: exited with status $es: $path"
    popd >/dev/null
done