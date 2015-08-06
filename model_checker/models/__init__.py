#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   -  Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   -  Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#   -  Neither the names of the contributors, nor their associated universities or
#      organizations may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from pyswitch_model import PyswitchModel
from pyswitch_3way_model import Pyswitch3WayModel
from eate_model import EateModel
from eate_model_10switch import EateModel10Switch
from twohosts_model import TwoHostsModel
from nice_model import NiceModel
# TestingPktSeqModel
from loadbalancer_model import LoadBalancerModel
from pyswitch_no_switch_state_match_model import PyswitchNoSwitchStateMatchModel
from pyswitch_benchmark_model import PyswitchBenchmarkModel
from eate_model_real_switch import EateModelRealSwitch
from loadbalancer_model_real_switch import LoadBalancerModelRealSwitch
from pyswitch_model_real_switch import PyswitchModelRealSwitch
from pyswitch_model_small_real_switch import PyswitchModelSmallRealSwitch

from test_model_real_switch import TestModelRealSwitch

models = {'PyswitchModel': PyswitchModel,
    'Pyswitch3WayModel': Pyswitch3WayModel,
    'EateModel': EateModel,
    'EateModel10Switch': EateModel10Switch,
    'TwoHostsModel': TwoHostsModel,
    'NiceModel': NiceModel,
    #'TestingPktSeqModel': TestingPktSeqModel,
    'PyswitchBenchmarkModel': PyswitchBenchmarkModel,
    'LoadBalancerModel': LoadBalancerModel,
    'PyswitchNoSwitchStateMatchModel': PyswitchNoSwitchStateMatchModel,
    'PyswitchModelRealSwitch' : PyswitchModelRealSwitch,
    'EateModelRealSwitch' : EateModelRealSwitch,
    'LoadBalancerModelRealSwitch' : LoadBalancerModelRealSwitch,
    'PyswitchModelSmallRealSwitch' : PyswitchModelSmallRealSwitch,
    'TestModelRealSwitch' : TestModelRealSwitch}

