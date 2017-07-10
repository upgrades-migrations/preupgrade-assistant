#!/bin/bash

CONFIG_FILES=/root/preupgrade/cleanconf

EXT=".preupg"
CWD=`pwd`
cd $CONFIG_FILES
for file in `find * -type f`
do
    NEW_FILE="/"$file
    if [ -f "$NEW_FILE" ]; then
        if [ -f "$NEW_FILE$EXT" ]; then
            echo "Config file $NEW_FILE was already copied to $NEW_FILE$EXT"
        else
            echo "Config file $NEW_FILE already exists. Move to $NEW_FILE$EXT"
            mv $NEW_FILE $NEW_FILE$EXT
        fi
    else
        echo "Config file $NEW_FILE does not exists."
    fi
    echo "Copy file $file to $NEW_FILE"
    cp -a $file $NEW_FILE
done
cd "$CWD"
