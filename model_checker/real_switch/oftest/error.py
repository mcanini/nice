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

# Python OpenFlow error wrapper classes

from cstruct import *



class hello_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for hello_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = OFPET_HELLO_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = self.header.pack()
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "hello_failed_error_msg\m"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class bad_request_error_msg(ofp_error_msg):
    """
    Wrapper class for bad_request error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = OFPET_BAD_REQUEST
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = self.header.pack()
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "bad_request_error_msg\m"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class bad_action_error_msg(ofp_error_msg):
    """
    Wrapper class for bad_action error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = OFPET_BAD_ACTION
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = self.header.pack()
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "bad_action_error_msg\m"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class flow_mod_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for flow_mod_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = OFPET_FLOW_MOD_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = self.header.pack()
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "flow_mod_failed_error_msg\m"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class port_mod_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for port_mod_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = OFPET_PORT_MOD_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = self.header.pack()
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "port_mod_failed_error_msg\m"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)


class queue_op_failed_error_msg(ofp_error_msg):
    """
    Wrapper class for queue_op_failed error message class

    Data members inherited from ofp_error_msg:
    @arg type
    @arg code
    @arg data: Binary string following message members
    
    """
    def __init__(self):
        ofp_error_msg.__init__(self)
        self.header = ofp_header()
        self.header.type = OFPT_ERROR
        self.type = OFPET_QUEUE_OP_FAILED
        self.data = ""

    def pack(self, assertstruct=True):
        self.header.length = self.__len__()
        packed = self.header.pack()
        packed += ofp_error_msg.pack(self)
        packed += self.data
        return packed

    def unpack(self, binary_string):
        binary_string = self.header.unpack(binary_string)
        binary_string = ofp_error_msg.unpack(self, binary_string)
        self.data = binary_string
        return ""

    def __len__(self):
        return OFP_HEADER_BYTES + OFP_ERROR_MSG_BYTES + len(self.data)

    def show(self, prefix=''):
        outstr = prefix + "queue_op_failed_error_msg\m"
        outstr += self.header.show(prefix + '  ')
        outstr += ofp_error_msg.show(self, prefix + '  ')
        outstr += prefix + "data is of length " + str(len(self.data)) + '\n'
        ##@todo Consider trying to parse the string
        return outstr

    def __eq__(self, other):
        if type(self) != type(other): return False
        return (self.header == other.header and
                ofp_error_msg.__eq__(self, other) and
                self.data == other.data)

    def __ne__(self, other): return not self.__eq__(other)

