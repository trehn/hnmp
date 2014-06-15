from datetime import timedelta
from sys import version_info

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import (
    Counter32,
    Gauge32,
    Integer,
    IpAddress,
    OctetString,
    TimeTicks,
)


def _convert_value_to_native(value):
    if isinstance(value, Counter32):
        return int(value.prettyPrint())
    if isinstance(value, Gauge32):
        return int(value.prettyPrint())
    if isinstance(value, Integer):
        return int(value.prettyPrint())
    if isinstance(value, IpAddress):
        return str(value.prettyPrint())
    if isinstance(value, OctetString):
        try:
            return value.asOctets().decode(value.encoding)
        except UnicodeDecodeError:
            return value.asOctets()
    if isinstance(value, TimeTicks):
        return timedelta(seconds=int(value.prettyPrint()) / 100.0)
    return value


def ipv4_address(string):
    if version_info >= (3,0):
        return ".".join([str(c) for c in string])
    else:
        return ".".join([str(ord(c)) for c in string])


def mac_address(string):
    if version_info >= (3,0):
        return ":".join([hex(c).lstrip("0x").zfill(2) for c in string])
    else:
        return ":".join([hex(ord(c)).lstrip("0x").zfill(2) for c in string])


class SNMP(object):
    def __init__(self, host, port=161, community="public"):
        self._cmdgen = cmdgen.CommandGenerator()
        self.host = host
        self.port = port
        self.community = community

    def get(self, oid):
        try:
            engine_error, pdu_error, pdu_error_index, objects = self._cmdgen.getCmd(
                cmdgen.CommunityData(self.community),
                cmdgen.UdpTransportTarget((self.host, self.port)),
                oid,
            )

        except Exception as e:
            raise SNMPError(e)
        if engine_error:
            raise SNMPError(engine_error)
        if pdu_error:
            raise SNMPError(pdu_error.prettyPrint())

        _, value = objects[0]
        value = _convert_value_to_native(value)
        return value


class SNMPError(Exception):
    pass
