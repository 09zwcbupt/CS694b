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

if __name__ == '__main__':
    shell = Popen( '/bin/bash', stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
    #print shell.stdin.fileno()
    write(shell, './run.test vm0\n')
    result = readall(shell, 1000)
    print result
    sleep(0.3)
    write(shell, 'ifconfig\n')
    result = readall(shell, 200)
    print result
    while True:
        try:
            sleep(2)
            write(shell, "top -b -n 1 | grep 'CPU:' | awk '{print $2}' | sed -n '1p'\n")
            result = readall(shell, 90)
            pos = result.find( '%' )
            if (pos != -1):
                print result[:pos]
            result = ''
        except KeyboardInterrupt:
            print 'cleaning up ' + str(shell.pid) + '\n'
            shell.terminate()
            break
    #os.kill(lastPid, signal.SIGINT)
    #print 'done \n'
