#!/bin/bash

die() {
    echo ${1}
    exit 1
}

mkdir -p /root/preupgrade/

PWD=${pwd}

TARBALL_PATH="/root/preupgrade/result.tar.gz"

curl -o ${TARBALL_PATH} "__INSERT_TARBALL_URL__" || die "Cannot download tarball!"

TEMP_DIR=$(mktemp -d)

cd $TEMP_DIR
tar -xf $TARBALL_PATH || die "Cannot unpack tarball!"

cd cleanconf

for file in $(find . -type f) ; do
    ABS_PATH=${file:1}
    SAVE_PATH="${ABS_PATH}.rpmsave"
    DIFF_FILENAME="$(basename ${file}).diff"
    [[ -f ${ABS_PATH} ]] && \
        cp -a ${ABS_PATH} ${SAVE_PATH}
    cp -a ${file} ${ABS_PATH}
    restorecon ${ABS_PATH}
    if [[ -f ${SAVE_PATH} ]] && [[ -f ${ABS_PATH} ]] ; then
        diff -u ${ABS_PATH} ${SAVE_PATH} || diff -u ${ABS_PATH} ${SAVE_PATH} >/root/preupgrade/${DIFF_FILENAME}
    fi
done

cd ${PWD}

rm -rf $TEMP_DIR
