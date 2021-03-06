# -*- coding: utf-8 -*-
#
# This file is part of the RoseNMS
#
# Copyright (C) 2012-2016 Craig Small <csmall@enc.com.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>
#
""" Messages for the IPC """

import zmq

LOGGER_SERVER = 'tcp://*:5000'
LOGGER_CLIENT = 'tcp://localhost:5000'
TSDB_ROUTER = 'tcp://*:5001'
TSDB_WORKER = 'tcp://localhost:5001'
CONTROL_SERVER = 'tcp://*:5002'
CONTROL_CLIENT = 'tcp://localhost:5002'
INFO_SERVER = 'tcp://*:5003'
INFO_CLIENT = 'tcp://localhost:5003'

# The inter-process sockets
CONTROL_SOCKET = 'inproc://control'
LOGGER_SOCKET = 'inproc://logger'
TSDBWORKER_SOCKET = 'inproc://tsdbworker'

IPC_END = "\x01"  # Sent from main process, the sub-process will die
INIT = "\x02"  # Child init sent to parent
CONF = "\x03"  # Parent sending config to child
READY = "\x04"  # Config/job consumed
IPC_INFO_REQ = '\x05'  # Info request
IPC_INFO_REP = '\x06'  # Info reply

IPC_LOG = "\x10"  # Sent to logger, log this message
TSDB_UPDATE = "\x11"  # Sent to tsdbworker - updates


# Common tasks
def init_and_config(socket):
    """
    Send the init message and block until we get the config message
    """
    socket.send(INIT)
    frames = socket.recv_multipart()
    if frames[0] != CONF or len(frames) != 2:
        return None
    return frames[1]


def control_server(context):
    """ Setup the control server socket that the main thread runs to
    control others
    """
    socket = context.socket(zmq.PUB)
    socket.bind(CONTROL_SOCKET)
    return socket


def control_client(context):
    """ Control socket for clients to listen on and be controlled """
    socket = context.socket(zmq.SUB)
    socket.connect(CONTROL_SOCKET)
    socket.setsockopt(zmq.SUBSCRIBE, '')
    return socket


def info_server(context):
    """ Socket from daemon to send info """
    socket = context.socket(zmq.REP)
    socket.bind(INFO_SERVER)
    return socket


def info_client(context):
    """ Socket to obtain info from daemon """
    socket = context.socket(zmq.REQ)
    socket.connect(INFO_CLIENT)
    return socket


def get_info(socket):
    """ Synchronously ask for daemon info and return the dictionary
    """
    socket.linger = 1000
    socket.send(IPC_INFO_REQ, zmq.NOBLOCK)
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    socks = dict(poller.poll(1000))
    if socks:
        if socks.get(socket) == zmq.POLLIN:
            frame = socket.recv(zmq.NOBLOCK)
            if frame == IPC_INFO_REP:
                return socket.recv_json(zmq.NOBLOCK)
    return None
