"""
Copyright (c) 2008 The Board of Trustees of
The Leland Stanford Junior University

We are making the OpenFlow specification and associated documentation (Software)
available for public use and benefit with the expectation that others will use,
modify and enhance the Software and contribute those enhancements back to the
community. However, since we would like to make the Software available for
broadest use, with as few restrictions as possible permission is hereby granted,
free of charge, to any person obtaining a copy of this Software to deal in the
Software under the copyrights without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Python OpenFlow action wrapper classes

from cstruct import *



class action_vendor(ofp_action_vendor_header):
    """
    Wrapper class for vendor action object

    Data members inherited from ofp_action_vendor_header:
    @arg type
    @arg len
    @arg vendor

    """
    def __init__(self):
        ofp_action_vendor_header.__init__(self)
        self.type = OFPAT_VENDOR
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_vendor\n"
        outstr += ofp_action_vendor_header.show(self, prefix)
        return outstr


class action_set_tp_dst(ofp_action_tp_port):
    """
    Wrapper class for set_tp_dst action object

    Data members inherited from ofp_action_tp_port:
    @arg type
    @arg len
    @arg tp_port

    """
    def __init__(self):
        ofp_action_tp_port.__init__(self)
        self.type = OFPAT_SET_TP_DST
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_tp_dst\n"
        outstr += ofp_action_tp_port.show(self, prefix)
        return outstr


class action_set_vlan_pcp(ofp_action_vlan_pcp):
    """
    Wrapper class for set_vlan_pcp action object

    Data members inherited from ofp_action_vlan_pcp:
    @arg type
    @arg len
    @arg vlan_pcp

    """
    def __init__(self):
        ofp_action_vlan_pcp.__init__(self)
        self.type = OFPAT_SET_VLAN_PCP
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_vlan_pcp\n"
        outstr += ofp_action_vlan_pcp.show(self, prefix)
        return outstr


class action_enqueue(ofp_action_enqueue):
    """
    Wrapper class for enqueue action object

    Data members inherited from ofp_action_enqueue:
    @arg type
    @arg len
    @arg port
    @arg queue_id

    """
    def __init__(self):
        ofp_action_enqueue.__init__(self)
        self.type = OFPAT_ENQUEUE
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_enqueue\n"
        outstr += ofp_action_enqueue.show(self, prefix)
        return outstr


class action_set_tp_src(ofp_action_tp_port):
    """
    Wrapper class for set_tp_src action object

    Data members inherited from ofp_action_tp_port:
    @arg type
    @arg len
    @arg tp_port

    """
    def __init__(self):
        ofp_action_tp_port.__init__(self)
        self.type = OFPAT_SET_TP_SRC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_tp_src\n"
        outstr += ofp_action_tp_port.show(self, prefix)
        return outstr


class action_set_nw_tos(ofp_action_nw_tos):
    """
    Wrapper class for set_nw_tos action object

    Data members inherited from ofp_action_nw_tos:
    @arg type
    @arg len
    @arg nw_tos

    """
    def __init__(self):
        ofp_action_nw_tos.__init__(self)
        self.type = OFPAT_SET_NW_TOS
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_tos\n"
        outstr += ofp_action_nw_tos.show(self, prefix)
        return outstr


class action_set_nw_dst(ofp_action_nw_addr):
    """
    Wrapper class for set_nw_dst action object

    Data members inherited from ofp_action_nw_addr:
    @arg type
    @arg len
    @arg nw_addr

    """
    def __init__(self):
        ofp_action_nw_addr.__init__(self)
        self.type = OFPAT_SET_NW_DST
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_dst\n"
        outstr += ofp_action_nw_addr.show(self, prefix)
        return outstr


class action_strip_vlan(ofp_action_header):
    """
    Wrapper class for strip_vlan action object

    Data members inherited from ofp_action_header:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_action_header.__init__(self)
        self.type = OFPAT_STRIP_VLAN
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_strip_vlan\n"
        outstr += ofp_action_header.show(self, prefix)
        return outstr


class action_set_dl_dst(ofp_action_dl_addr):
    """
    Wrapper class for set_dl_dst action object

    Data members inherited from ofp_action_dl_addr:
    @arg type
    @arg len
    @arg dl_addr

    """
    def __init__(self):
        ofp_action_dl_addr.__init__(self)
        self.type = OFPAT_SET_DL_DST
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_dl_dst\n"
        outstr += ofp_action_dl_addr.show(self, prefix)
        return outstr


class action_set_nw_src(ofp_action_nw_addr):
    """
    Wrapper class for set_nw_src action object

    Data members inherited from ofp_action_nw_addr:
    @arg type
    @arg len
    @arg nw_addr

    """
    def __init__(self):
        ofp_action_nw_addr.__init__(self)
        self.type = OFPAT_SET_NW_SRC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_nw_src\n"
        outstr += ofp_action_nw_addr.show(self, prefix)
        return outstr


class action_set_vlan_vid(ofp_action_vlan_vid):
    """
    Wrapper class for set_vlan_vid action object

    Data members inherited from ofp_action_vlan_vid:
    @arg type
    @arg len
    @arg vlan_vid

    """
    def __init__(self):
        ofp_action_vlan_vid.__init__(self)
        self.type = OFPAT_SET_VLAN_VID
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_vlan_vid\n"
        outstr += ofp_action_vlan_vid.show(self, prefix)
        return outstr


class action_set_dl_src(ofp_action_dl_addr):
    """
    Wrapper class for set_dl_src action object

    Data members inherited from ofp_action_dl_addr:
    @arg type
    @arg len
    @arg dl_addr

    """
    def __init__(self):
        ofp_action_dl_addr.__init__(self)
        self.type = OFPAT_SET_DL_SRC
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_set_dl_src\n"
        outstr += ofp_action_dl_addr.show(self, prefix)
        return outstr


class action_output(ofp_action_output):
    """
    Wrapper class for output action object

    Data members inherited from ofp_action_output:
    @arg type
    @arg len
    @arg port
    @arg max_len

    """
    def __init__(self):
        ofp_action_output.__init__(self)
        self.type = OFPAT_OUTPUT
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "action_output\n"
        outstr += ofp_action_output.show(self, prefix)
        return outstr

action_class_list = (
    action_vendor,
    action_set_tp_dst,
    action_set_vlan_pcp,
    action_enqueue,
    action_set_tp_src,
    action_set_nw_tos,
    action_set_nw_dst,
    action_strip_vlan,
    action_set_dl_dst,
    action_set_nw_src,
    action_set_vlan_vid,
    action_set_dl_src,
    action_output)
