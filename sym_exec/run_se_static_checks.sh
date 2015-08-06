#!/bin/sh

PYLINT=`which pylint`

if [ -z $PYLINT ]; then
	echo "You need to install pylint for this to work"
	exit
fi

export PYTHONPATH=.:../common_modules:sym_exec_lib:symbolic:$PYTHONPATH
$PYLINT --rcfile=./pylint.rc `find symbolic -name "*.py"` sym_exec.py `find sym_exec_lib -name "*.py"`

