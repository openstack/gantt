# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010 Openstack, LLC.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Scheduler Classes
"""

import logging
import random
import sys
import time

from nova import exception
from nova import flags
from nova.datastore import Redis

FLAGS = flags.FLAGS
flags.DEFINE_integer('node_down_time',
                     60,
                     'seconds without heartbeat that determines a compute node to be down')


class Scheduler(object):
    """
    The base class that all Scheduler clases should inherit from
    """

    @property
    def compute_nodes(self):
        return [identifier.split(':')[0] for identifier in Redis.instance().smembers("daemons") if (identifier.split(':')[1] == "nova-compute")]

    def compute_node_is_up(self, node):
        time_str = Redis.instance().hget('%s:%s:%s' % ('daemon', node, 'nova-compute'), 'updated_at')
        # Would be a lot easier if we stored heartbeat time in epoch :)
        return(time_str and
           (time.time() - (int(time.mktime(time.strptime(time_str.replace('Z', 'UTC'), '%Y-%m-%dT%H:%M:%S%Z'))) - time.timezone) < FLAGS.node_down_time))

    def compute_nodes_up(self):
        return [node for node in self.compute_nodes if self.compute_node_is_up(node)]

    def pick_node(self, instance_id, **_kwargs):
        """You DEFINITELY want to define this in your subclass"""
        raise NotImplementedError("Your subclass should define pick_node")

class RandomScheduler(Scheduler):
    """
    Implements Scheduler as a random node selector
    """

    def __init__(self):
        super(RandomScheduler, self).__init__()

    def pick_node(self, instance_id, **_kwargs):
        nodes = self.compute_nodes_up()
        return nodes[int(random.random() * len(nodes))]

class BestFitScheduler(Scheduler):
    """
    Implements Scheduler as a best-fit node selector
    """

    def __init__(self):
        super(BestFitScheduler, self).__init__()

    def pick_node(self, instance_id, **_kwargs):
        raise NotImplementedError("BestFitScheduler is not done yet")

