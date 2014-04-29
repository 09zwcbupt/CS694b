#!/bin/python

import os
import signal
from time import sleep
from select import poll, POLLIN
from subprocess import call, check_call, Popen, PIPE, STDOUT

readbuf = ''
waiting = False
lastCmd = None
lastPid = None

def read( shell, maxbytes=1024 ):
    """Buffered read from node, non-blocking.
       maxbytes: maximum number of bytes to return"""
    global readbuf
    count = len( readbuf )
    if count < maxbytes:
        data = os.read( shell.stdout.fileno(), maxbytes - count )
        readbuf += data
    if maxbytes >= len( readbuf ):
        result = readbuf
        readbuf = ''
    else:
        result = readbuf[ :maxbytes ]
        readbuf = readbuf[ maxbytes: ]
    return result

def readline( shell ):
    """Buffered readline from node, non-blocking.
       returns: line (minus newline) or None"""
    global readbuf
    readbuf += read( shell, 1024 )
    if '\n' not in readbuf:
        return None
    pos = readbuf.find( '\n' )
    line = readbuf[ 0: pos ]
    readbuf = readbuf[ pos + 1: ]
    return line

def write( shell, data ):
    """Write data to node.
       data: string"""
    #print 'cmd: ' + data
    global waiting
    os.write( shell.stdin.fileno(), data )
    waiting = True

def readall(shell, timeout):
    global waiting
    data = ''
    nodePoller = poll()
    nodePoller.register(shell.stdout, POLLIN)
    while waiting:
        event = nodePoller.poll(timeout)
        if event == []:
            waiting = False
        for fd, flag in event:
            #print fd, flag
            if flag & POLLIN:
                data += read(shell)
    return data

def get_vm_cmd(shell_list):
    print 'starting vm'+str(len(shell_list))
    return './run vm'+str(len(shell_list))+'\n'

def get_vm_name(shell, name_dict):
    return name_dict[shell.pid]

if __name__ == '__main__':
    shell_list = []# bash<->vm
    shell_stat = {}# key:shell obj, value: high usage/no response
    vm_name = {}
    new_vm = None
    # run the first VM
    shell = Popen( '/bin/bash', stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
    write(shell, get_vm_cmd(shell_list))
    shell_list.append(shell)
    shell_stat[shell] = 0#time of high usage/no response
    vm_name[shell.pid] = 'vm0'
    result = readall(shell, 1000)
    print result
    sleep(0.3)
    write(shell, 'ifconfig\n')
    result = readall(shell, 200)
    print result
    while True:
        try:
            print '\n-----------------------------------'
            if (new_vm != None):
                # new vm on line, put it in list/dict
                vm_name[new_vm.pid]= 'vm'+str(len(shell_list))
                shell_list.append(new_vm)
                shell_stat[new_vm] = 0
                write(new_vm, 'ifconfig\n')
                result = readall(new_vm, 2000)
                print result
                new_vm=None
            sleep(2)
            for shell in shell_list:
                write(shell, "top -b -n 1 | grep 'CPU:' | awk '{print $2}' | sed -n '1p'\n")
                result = readall(shell, 10)
                pos = result.find( '%' )
                if (pos != -1):
                    if(pos-4>0 and result[pos-4]=='\n'): print get_vm_name(shell,vm_name), result[pos-3:pos]
                    else: print get_vm_name(shell, vm_name), result[0 if (pos-4<0) else pos-4:pos]
                    shell_stat[shell] = 0
                else:
                    shell_stat[shell]+=1
                    if(shell_stat[shell]>2):
                        #allocate new VM
                        new_vm = Popen( '/bin/bash', stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
                        write(new_vm, get_vm_cmd(shell_list))
                    print get_vm_name(shell, vm_name), 'miss'
                result = ''
        except KeyboardInterrupt:
            for shell in shell_list:
                print 'cleaning up ' + str(shell.pid)
                shell.terminate()
            if new_vm != None:
                new_vm.terminate()
            break
    #os.kill(lastPid, signal.SIGINT)
    #print 'done \n'
