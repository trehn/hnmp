HNMP is a high-level Python library to ease the pain of retrieving and processing data from SNMP-capable devices such as network switches, routers, and printers. It's not meant to provide everything SNMP has to offer, but to get rid of most of the suck inherent to writing Munin or Icinga plugins that process SNMP data.

HNMP is meant to be used like this:

1. acquire MIB files (optional, some luck required)
2. use a MIB browser application like [this freeish and cross-platform one](http://ireasoning.com/mibbrowser.shtml) by iREASONING to figure out the OIDs you're interested in
3. use HNMP to retrieve your data and do some light processing
4. put man on moon :rocket:

Usage
-----

```python
>>> from hnmp import SNMP
>>>
>>> snmp = SNMP("example.com")

# get a single value
>>> uptime = snmp.get("1.3.6.1.2.1.1.3.0")
>>> uptime
datetime.timedelta(412, 29152)

# build a table
>>> wifi_clients = snmp.table(
>>>     "1.3.6.1.4.1.14179.2.1.4.1",
>>>     columns={
>>>         3: "username",
>>>         25: "protocol",
>>>     },
>>>     column_value_mapping={
>>>         "protocol": {
>>>             3: "802.11g",
>>>             6: "802.11n",
>>>         },
>>>     },
>>> )
>>>
>>> table.columns["username"]
("jdoe", "rms", "bwayne")
>>> table.columns["protocol"]
("802.11g", "802.11n", "802.11n")
>>> table.rows[0]["username"]
"jdoe"

# conveniently count column values
>>> table.columns["protocol"]
("802.11g", "802.11n", "802.11n")
>>> table.columns["protocol"].value_count
{"802.11g": 1, "802.11n": 2}
```
