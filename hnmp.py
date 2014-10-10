from datetime import timedelta
from inspect import isgenerator
from sys import version_info

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import (
    Counter32,
    Counter64,
    Gauge32,
    Integer,
    Integer32,
    Unsigned32,
    IpAddress,
    OctetString,
    TimeTicks,
    Bits,
)

TYPES = {
    'Bits': Bits,
    'Counter32': Counter32,
    'Counter64': Counter64,
    'Gauge32': Gauge32,
    'Integer': Integer,
    'Integer32': Integer32,
    'IpAddress': IpAddress,
    'OctetString': OctetString,
    'TimeTicks': TimeTicks,
    'Unsigned32': Unsigned32,
}


def cached_property(prop):
    """
    A replacement for the property decorator that will only compute the
    attribute's value on the first call and serve a cached copy from
    then on.
    """
    def cache_wrapper(self):
        if not hasattr(self, "_cache"):
            self._cache = {}
        if not prop.__name__ in self._cache:
            return_value = prop(self)
            if isgenerator(return_value):
                return_value = tuple(return_value)
            self._cache[prop.__name__] = return_value
        return self._cache[prop.__name__]
    return property(cache_wrapper)


def _convert_value_to_native(value):
    """
    Converts pysnmp objects into native Python objects.
    """
    if isinstance(value, Counter32):
        return int(value.prettyPrint())
    if isinstance(value, Counter64):
        return int(value.prettyPrint())
    if isinstance(value, Gauge32):
        return int(value.prettyPrint())
    if isinstance(value, Integer):
        return int(value.prettyPrint())
    if isinstance(value, Integer32):
        return int(value.prettyPrint())
    if isinstance(value, Unsigned32):
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


class CountingTuple(tuple):
    """
    A tuple that automatically counts its values.
    """
    @cached_property
    def value_count(self):
        values = {}
        for value in self:
            try:
                values[value] += 1
            except KeyError:
                values[value] = 1
        return values


def ipv4_address(string):
    if version_info >= (3,0):
        return ".".join([str(c) for c in string])
    else:
        return ".".join([str(ord(c)) for c in string])


def is_ipv4_address(value):
    try:
        c1, c2, c3, c4 = value.split(".")
        assert 0 <= int(c1) <= 255
        assert 0 <= int(c2) <= 255
        assert 0 <= int(c3) <= 255
        assert 0 <= int(c4) <= 255
        return True
    except:
        return False


def mac_address(string):
    if version_info >= (3,0):
        return ":".join([hex(c).lstrip("0x").zfill(2) for c in string])
    else:
        return ":".join([hex(ord(c)).lstrip("0x").zfill(2) for c in string])


class SNMP(object):
    """
    Represents a 'connection' to a certain SNMP host.
    """
    def __init__(self, host, port=161, community="public"):
        self._cmdgen = cmdgen.CommandGenerator()
        self.host = host
        self.port = port
        self.community = community

    def get(self, oid):
        """
        Get a single OID value.
        """
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

    def table(self, oid, columns=None, column_value_mapping=None, non_repeaters=0,
              max_repetitions=20, fetch_all_columns=True):
        """
        Get a table of values with the given OID prefix.
        """
        base_oid = oid.strip(".")

        if not fetch_all_columns and not columns:
            raise ValueError("please use the columns argument to "
                             "indicate which columns to fetch")

        if fetch_all_columns:
            columns_to_fetch = [""]
        else:
            columns_to_fetch = ["." + str(col_id) for col_id in columns.keys()]

        full_obj_table = []

        for col in columns_to_fetch:
            try:
                engine_error, pdu_error, pdu_error_index, obj_table = self._cmdgen.bulkCmd(
                    cmdgen.CommunityData(self.community),
                    cmdgen.UdpTransportTarget((self.host, self.port)),
                    non_repeaters,
                    max_repetitions,
                    oid + col,
                )

            except Exception as e:
                raise SNMPError(e)
            if engine_error:
                raise SNMPError(engine_error)
            if pdu_error:
                raise SNMPError(pdu_error.prettyPrint())

            # remove any trailing rows from the next subtree
            try:
                while not obj_table[-1][0][0].prettyPrint().lstrip(".").startswith(
                    base_oid + col + "."
                ):
                    obj_table.pop()
            except IndexError:
                pass

            # append this column to full result
            full_obj_table += obj_table

        t = Table(columns=columns, column_value_mapping=column_value_mapping)

        for row in full_obj_table:
            for name, value in row:
                oid = name.prettyPrint().strip(".")
                value = _convert_value_to_native(value)
                column, row_id = oid[len(base_oid) + 1:].split(".", 1)
                t._add_value(int(column), row_id, value)

        return t

    def set(self, oid, value, value_type=None):
        """
            Sets a single OID value. If you do not pass value_type hnmp will
        try to guess the correct type of value. Autodetection now supported
        only for few some types as:
            int and float (as Integer, fractional part will be discarded).
            IPv4 address (as IpAddress).
            str (as OctetString).
        Howewer, you can pass any pysnmp.proto.rfc1902 type as third argument
        to force type recognition.
        
        Unfortunately, pysnmp does not support SNMP FLOAT type so please
        use Integer instead.
        """
        if value_type is None:
            if type(value) is int:
                data = Integer(value)
            elif type(value) is float:
                data = Integer(value)
            elif type(value) is str:
                if is_ipv4_address(value):
                    data = IpAddress(value)
                else:
                    data = OctetString(value)
            else:
                raise ValueError("Type detection failed." +\
                                 " Try to specify type by hands.")
        else:
            if not value_type in TYPES:
                raise ValueError('Type %s is not supported.' % value_type)
            data = TYPES[value_type](value)
        try:
            engine_error, pdu_error, pdu_error_index, objects = self._cmdgen.setCmd(
                cmdgen.CommunityData(self.community),
                cmdgen.UdpTransportTarget((self.host, self.port)),
                (oid, data),
            )
            if engine_error:
                raise SNMPError(engine_error)
            if pdu_error:
                raise SNMPError(pdu_error.prettyPrint())

        except Exception as e:
            raise SNMPError(e)

        _, value = objects[0]
        value = _convert_value_to_native(value)
        return value


class SNMPError(Exception):
    pass


class Table(object):
    def __init__(self, columns=None, column_value_mapping=None):
        self._column_aliases = {} if columns is None else columns
        self._column_value_mapping = {} if column_value_mapping is None else column_value_mapping
        self._rows = {}

    def _add_value(self, raw_column, row_id, value):
        column = self._column_aliases.get(raw_column, raw_column)
        try:
            value = self._column_value_mapping[column][value]
        except KeyError:
            pass
        try:
            self._rows[row_id][column] = value
        except KeyError:
            self._rows[row_id] = {column: value}

    @cached_property
    def columns(self):
        c = {}
        for row_id, values in self._rows.items():
            for column, value in values.items():
                try:
                    c[column].append(value)
                except KeyError:
                    c[column] = [value]
        for column in tuple(c.keys()):
            c[column] = CountingTuple(c[column])
        return c

    @cached_property
    def rows(self):
        r = []
        for row_id, values in self._rows.items():
            values['_row_id'] = row_id
            r.append(values)
        return tuple(r)
