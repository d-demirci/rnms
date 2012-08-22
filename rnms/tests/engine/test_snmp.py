# -*- coding: utf-8 -*-
"""
Functional test suite for the root controller.

This is an example of how functional tests can be written for controllers.

As opposed to a unit-test, which test a small unit of functionality,
functional tests exercise the whole application and its WSGI stack.

Please read http://pythonpaste.org/webtest/ for more information.

"""
from nose.tools import assert_true, nottest, eq_

from rnms.lib.snmp import SNMPEngine
class DummyHost(object):
    mgmt_address = ''
    community_ro = {}
    def __init__(self, ip, snmpver, snmpcomm):
        self.mgmt_address = ip
        self.community_ro[0] = snmpver
        self.community_ro[1] = snmpcomm

def my_callback1(value, host, kwargs, error=None):
    if 'obj' not in kwargs:
        assert False
        return
    kwargs['obj'].results.append(value)

class TestSNMP(object):
    """ Base unit for SNMP testing """
    sysobjid_oid = (1,3,6,1,2,1,1,2,0)
    results = []
    expected_sysobjid = "1.3.6.1.4.1.8072.3.2.10"

    def setUp(self):
        """ Setup the SNMP engine """
        self.snmp_engine = SNMPEngine()
        self.results = []

    def poll(self):
        while (self.snmp_engine.poll()):
            pass

    def test_fetch(self):
        """ Simple SNMP fetch of SysObjectID """
        host = DummyHost("127.0.0.1", 2, "public")
        self.snmp_engine.get_str(host, self.sysobjid_oid, my_callback1, obj=self )
        self.poll()
        print(self.results)
        eq_(self.results, [self.expected_sysobjid,])

    def test_default_bad_comm(self):
        """ Simple SNMP fetch returns default with bad community"""
        host = DummyHost("127.0.0.1", 2, "badcomm")
        self.snmp_engine.get_str(host, self.sysobjid_oid, my_callback1, default="42", obj=self )
        self.poll()
        eq_(self.results, ["42"])

    def test_default_bad_oid(self):
        """ Simple SNMP fetch returns default with bad OID"""
        host = DummyHost("127.0.0.1", 2, "public")
        self.snmp_engine.get_str(host, '1.3.6.42.41.40', my_callback1, default="42", obj=self )
        self.poll()
        eq_(self.results, ["42"])