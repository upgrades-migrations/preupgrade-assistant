TEMP_DIR=$(mktemp -d)
cd ${TEMP_DIR}
PREUPGRADE_LOG=/var/log/preupgrade.log
touch ${PREUPGRADE_LOG}
TAR_BALL=preupgrade.tar.gz
echo "{tar_ball}" > data
base64 --decode data > ${TAR_BALL}
tar -xzvf ${TAR_BALL}
ls -laR >> ${PREUPGRADE_LOG}
PWD=${pwd}
cd cleanconf
for file in $(find . -type f)
do
    ABS_PATH=${file:1}
    SAVE_PATH="${ABS_PATH}.rpmsave"
    DIFF_FILENAME="$(basename ${file}).diff"
    echo "Comparing file ${file} against ${SAVE_PATH}" >> ${PREUPGRADE_LOG}
    echo "Diff output is stored in ${TEMP_DIR}/${DIFF_FILENAME}" >> ${PREUPGRADE_LOG}
    [[ -f ${ABS_PATH} ]] && \
        cp -a ${ABS_PATH} ${SAVE_PATH}
    cp -a ${file} ${ABS_PATH}
    restorecon ${ABS_PATH}
    if [[ -f ${SAVE_PATH} ]] && [[ -f ${ABS_PATH} ]]
    then
        diff -u ${ABS_PATH} ${SAVE_PATH} || diff -u ${ABS_PATH} ${SAVE_PATH} > ${TEMP_DIR}/${DIFF_FILENAME}
    fi
done
cd ${PWD}
KS_SCRIPTS="kickstart/scripts"
cd KS_SCRIPTS
for file in $(find . -type f -executable)
do
    echo "Running script ${file} ..." >> ${PREUPGRADE_LOG}
    ${file}
    echo "Running script ${file} done" >> ${PREUPGRADE_LOG}
done
cd ${PWD}
