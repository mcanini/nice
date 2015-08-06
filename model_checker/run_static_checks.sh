#!/bin/sh

PYLINT=`which pylint`

if [ -z $PYLINT ]; then
	echo "You need to install pylint for this to work"
	exit
fi

export PYTHONPATH=.:nox_lib:lib:../common_modules:$PYTHONPATH
$PYLINT --rcfile=../sym_exec/pylint.rc `find clients -name "*.py"` *.py `find lib -name "*.py"` `find of_controller -name "*.py"` `find of_switch -name "*.py"` `find invariants -name "*.py"` `find models -name "*.py"`

