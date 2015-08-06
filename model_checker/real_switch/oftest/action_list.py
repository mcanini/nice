"""
OpenFlow actions list class

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

from action import *
from cstruct import ofp_header
import copy

# # Map OFP action identifiers to the actual structures used on the wire
# action_object_map = {
#     OFPAT_OUTPUT                        : ofp_action_output,
#     OFPAT_SET_VLAN_VID                  : ofp_action_vlan_vid,
#     OFPAT_SET_VLAN_PCP                  : ofp_action_vlan_pcp,
#     OFPAT_STRIP_VLAN                    : ofp_action_header,
#     OFPAT_SET_DL_SRC                    : ofp_action_dl_addr,
#     OFPAT_SET_DL_DST                    : ofp_action_dl_addr,
#     OFPAT_SET_NW_SRC                    : ofp_action_nw_addr,
#     OFPAT_SET_NW_DST                    : ofp_action_nw_addr,
#     OFPAT_SET_NW_TOS                    : ofp_action_nw_tos,
#     OFPAT_SET_TP_SRC                    : ofp_action_tp_port,
#     OFPAT_SET_TP_DST                    : ofp_action_tp_port,
#     OFPAT_ENQUEUE                       : ofp_action_enqueue
# }

action_object_map = {
    OFPAT_OUTPUT                        : action_output,
    OFPAT_SET_VLAN_VID                  : action_set_vlan_vid,
    OFPAT_SET_VLAN_PCP                  : action_set_vlan_pcp,
    OFPAT_STRIP_VLAN                    : action_strip_vlan,
    OFPAT_SET_DL_SRC                    : action_set_dl_src,
    OFPAT_SET_DL_DST                    : action_set_dl_dst,
    OFPAT_SET_NW_SRC                    : action_set_nw_src,
    OFPAT_SET_NW_DST                    : action_set_nw_dst,
    OFPAT_SET_NW_TOS                    : action_set_nw_tos,
    OFPAT_SET_TP_SRC                    : action_set_tp_src,
    OFPAT_SET_TP_DST                    : action_set_tp_dst,
    OFPAT_ENQUEUE                       : action_enqueue,
    OFPAT_VENDOR                        : action_vendor
}

class action_list(object):
    """
    Maintain a list of actions

    Data members:
    @arg actions: An array of action objects such as action_output, etc.

    Methods:
    @arg pack: Pack the structure into a string
    @arg unpack: Unpack a string to objects, with proper typing
    @arg add: Add an action to the list; you can directly access
    the action member, but add will validate that the added object 
    is an action.

    """

    def __init__(self):
        self.actions = []

    def pack(self):
        """
        Pack a list of actions

        Returns the packed string
        """

        packed = ""
        for act in self.actions:
            packed += act.pack()
        return packed

    def unpack(self, binary_string, bytes=None):
        """
        Unpack a list of actions
        
        Unpack actions from a binary string, creating an array
        of objects of the appropriate type

        @param binary_string The string to be unpacked

        @param bytes The total length of the action list in bytes.  
        Ignored if decode is True.  If None and decode is false, the
        list is assumed to extend through the entire string.

        @return The remainder of binary_string that was not parsed

        """
        if bytes == None:
            bytes = len(binary_string)
        bytes_done = 0
        count = 0
        cur_string = binary_string
        while bytes_done < bytes:
            hdr = ofp_action_header()
            hdr.unpack(cur_string)
            if hdr.len < OFP_ACTION_HEADER_BYTES:
                print "ERROR: Action too short"
                break
            if not hdr.type in action_object_map.keys():
                print "WARNING: Skipping unknown action ", hdr.type, hdr.len
            else:
                self.actions.append(action_object_map[hdr.type]())
                self.actions[count].unpack(cur_string)
                count += 1
            cur_string = cur_string[hdr.len:]
            bytes_done += hdr.len
        return cur_string

    def add(self, action):
        """
        Add an action to an action list

        @param action The action to add

        @return True if successful, False if not an action object

        """
        if isinstance(action, action_class_list):
            tmp = copy.deepcopy(action)
            self.actions.append(tmp)
            return True
        return False

    def remove_type(self, type):
        """
        Remove the first action on the list of the given type

        @param type The type of action to search

        @return The object removed, if any; otherwise None

        """
        for index in xrange(len(self.actions)):
            if self.actions[index].type == type:
                return self.actions.pop(index)
        return None

    def find_type(self, type):
        """
        Find the first action on the list of the given type

        @param type The type of action to search

        @return The object with the matching type if any; otherwise None

        """
        for index in xrange(len(self.actions)):
            if self.actions[index].type == type:
                return self.actions[index]
        return None

    def extend(self, other):
        """
        Add the actions in other to this list

        @param other An object of type action_list whose
        entries are to be merged into this list

        @return True if successful.  If not successful, the list
        may have been modified.

        @todo Check if this is proper deep copy or not

        """
        for act in other.actions:
            if not self.add(act):
                return False
        return True
        
    def __len__(self):
        length = 0
        for act in self.actions:
            length += act.__len__()
        return length

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.actions != other.actions: return False
        return True

    def __ne__(self, other): return not self.__eq__(other)
        
    def show(self, prefix=''):
        outstr = prefix + "Action List with " + str(len(self.actions)) + \
            " actions\n"
        count = 0
        for obj in self.actions:
            count += 1
            outstr += prefix + "  Action " + str(count) + ": \n"
            outstr += obj.show(prefix + '    ')
        return outstr
