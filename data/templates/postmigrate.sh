
TEMP_DIR={TEMPORARY_PREUPG_DIR}
mkdir -p ${TEMP_DIR}
cd ${TEMP_DIR}
PREUPGRADE_LOG=/var/log/preupgrade.log
touch ${PREUPGRADE_LOG}
TAR_BALL=preupgrade.tar.gz
echo "INFO: prepare tarball ${TAR_BALL}." >> ${PREUPGRADE_LOG}
echo "{tar_ball}" > data
base64 --decode data > ${TAR_BALL}
echo "INFO: unpack tarball ${TAR_BALL}." >> ${PREUPGRADE_LOG}
tar --selinux -xzvf ${TAR_BALL}
# create symlinks
ln -s {RESULT_NAME}/cleanconf cleanconf
ln -s {RESULT_NAME}/dirtyconf dirtyconf
ln -s {RESULT_NAME}/kickstart kickstart
ln -s {RESULT_NAME}/postmigrate.d postmigrate.d
ln -s {RESULT_NAME}/noauto_postupgrade.d noauto_postupgrade.d

ls -laR >> ${PREUPGRADE_LOG}
cd {RESULT_NAME}/cleanconf
echo "INFO: Restore configuration files from ${PWD} directory." >> ${PREUPGRADE_LOG}
for file in $(find . -type f)
do
    ABS_PATH=${file:1}
    SAVE_PATH="${ABS_PATH}.preupg_save"
    if [[ -f "${ABS_PATH}" ]]
    then
        echo "INFO: Backing up the clean system configuration file '${ABS_PATH}' to '${SAVE_PATH}'." >> ${PREUPGRADE_LOG}
        cp -a ${ABS_PATH} ${SAVE_PATH}
    fi

    if [[ ! -d "$(dirname "$ABS_PATH")" ]]
    then
        # create the directory - maybe doesn't exist yet because the rpm
        # has not been installed yet
        mkdir -p "$(dirname "$ABS_PATH")"
    fi

    echo "INFO: Restoring configuration file of the migrated system '${ABS_PATH}'." >> ${PREUPGRADE_LOG}
    cp -a ${file} ${ABS_PATH}
    restorecon ${ABS_PATH}
done

echo "INFO: process postmigrate scripts." >> ${PREUPGRADE_LOG}
cd ${TEMP_DIR}/{RESULT_NAME}/postmigrate.d
for file in $(find . -type f -executable)
do
    echo "Running script ${file} ..." >> ${PREUPGRADE_LOG}
    ${file}
    echo "Running script ${file} done" >> ${PREUPGRADE_LOG}
done
