#!/bin/bash
top -b -n 1 | grep 'CPU:' | awk '{print $2}' | sed -n '1p'
