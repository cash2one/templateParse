#!/usr/bin/env python
# -*- coding: utf-8 -*-

#***************************************************************************
# * 
# * Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#* 
# **************************************************************************/
#* @file server.py
#* @author zhongzhiwei01(com@baidu.com)
#* @date 2014/10/31 11:39:34
  
import os
import sys
import subprocess

import rpyc
from rpyc.utils.server import ThreadedServer


class MyService(rpyc.Service):
    """
    MyService    -the main class.
    """
    def exposed_run_phantomjs(self, url_addr):
        if not os.path.isfile('is_running.app'):
            file = open('is_running.app', 'w')
            file.write('The template program is running.')
            file.close()
            child = subprocess.Popen(['python', 'parse_template.py', '-l', url_addr], stdout=subprocess.PIPE)
            (output,errput)=child.communicate()
            child.wait()
            os.remove('is_running.app')
            return output
        else:
            return "当前有用户正在使用，请稍后再试！"

if __name__ == "__main__":
    my_process = ThreadedServer(MyService, port=9999, auto_register=False)
    my_process.start()
