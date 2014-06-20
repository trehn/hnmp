try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="hnmp",
    version="0.3.0",
    description="High-level Python SNMP library",
    long_description="HNMP is a high-level Python library to ease the pain of retrieving and processing data from SNMP-capable devices such as network switches, routers, and printers. It's not meant to provide everything SNMP has to offer, but to get rid of most of the suck inherent to writing Munin or Icinga plugins that process SNMP data.",
    author="Torsten Rehn",
    author_email="torsten@rehn.email",
    license="ISC",
    url="https://github.com/trehn/hnmp",
    keywords=["SNMP", "OID", "MIB"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
    ],
    install_requires=[
        "pysnmp >= 4.2.1",
    ],
    py_modules=['hnmp'],
)
