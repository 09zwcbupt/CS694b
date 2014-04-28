#!/bin/sh
set -x

switch=br0
sudo ovs-vsctl del-port br0 $1

if [ -n "$1" ];then
        sudo /usr/bin/sudo /usr/sbin/tunctl -u `whoami` -t $1
        /usr/bin/sudo /sbin/ip link set $1 up
        sleep 0.1s
        sudo /usr/bin/sudo ovs-vsctl add-port $switch $1
        exit 0
else
        echo "Error: no interface specified"
        exit 1
fi
