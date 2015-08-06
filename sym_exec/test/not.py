# vim: set expandtab ts=4 sw=4:
#
def not_inside_if(in1, in2, in3):
    if not in1:
        if not in2:
            return 0
        else:
            return 1
    elif not in2:
        if not (in3 & 3):
            return 2
        else:
            return 3
    else:
        return 4
