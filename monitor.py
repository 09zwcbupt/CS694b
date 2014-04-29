import os
import signal
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

def sendInt( shellf, sig=signal.SIGINT ):
    "Interrupt running command."
    global lastPid
    if lastPid:
        print lastPid
        try:
            os.kill( lastPid, sig )
        except OSError:
            pass

def readall(shell):
    global waiting
    data = ''
    nodePoller = poll()
    nodePoller.register(shell.stdout, POLLIN)
    while waiting:
        event = nodePoller.poll(50)
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
    write(shell, 'ps ax\n')
    result = readall(shell)
    print result
    #print 'done \n'
