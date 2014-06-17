# -*- coding: utf-8 -*-

import logging
import subprocess


logger = logging.getLogger('preup_ui')


def run_subprocess(cmd, log=False, shell=False, to_stdout=False):
    sp = subprocess.Popen(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          shell=shell)
    while sp.poll() == None:
        if log or to_stdout:
            out = sp.stdout.readline().strip().decode('utf8')
            if log:
                logger.info(out)
            if to_stdout:
                print out
    logger.info('Cmd: \'%s\' finished with exit code: %d', ' '.join(cmd), sp.returncode)
    return sp.returncode