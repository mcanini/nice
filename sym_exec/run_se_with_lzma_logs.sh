#!/bin/bash

# This script runs the se and save the logs in compressed files

i=$1

if [ -z $1 ]; then
	echo "Specify the number of invocations"
	exit
fi

mkdir -p output
rm -f output/pyse$i.pipe

mkfifo output/pyse$i.pipe
lzcat -z -9 < output/pyse$i.pipe > output/pyse$i.log.lzma &
./sym_exec.py -i $i -l output/pyse$i.pipe examples/pyswitch.py

rm -f output/pyse$i.pipe

