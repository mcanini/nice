#!/bin/bash

for t in many_branches shallow_branches loop logical_op elseif dictionary count_packets expressions not assign; do
	./sym_exec.py -q -l /dev/null test $t
done

