#!/bin/bash
# Formating raw disk image to qcow2 format (which support snapshot)
qemu-img convert -O qcow2 hd.img hd.img.qcow2
