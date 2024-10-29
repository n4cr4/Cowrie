# Copyright (c) 2009-2014 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

"""
This module contains ...
"""

from __future__ import annotations

from configparser import NoOptionError
import time
import random

from twisted.conch.openssh_compat import primes
from twisted.conch.ssh import factory, keys, transport
from twisted.cred import portal as tp
from twisted.python import log

from cowrie.core.config import CowrieConfig
from cowrie.ssh import connection
from cowrie.ssh import keys as cowriekeys
from cowrie.ssh import transport as shellTransport
from cowrie.ssh.userauth import HoneyPotSSHUserAuthServer
from cowrie.ssh_proxy import server_transport as proxyTransport
from cowrie.ssh_proxy.userauth import ProxySSHAuthServer


class CowrieSSHFactory(factory.SSHFactory):
    """
    This factory creates HoneyPotSSHTransport instances
    They listen directly to the TCP port
    """

    starttime: float | None = None
    privateKeys: dict[bytes, bytes]
    publicKeys: dict[bytes, bytes]
    primes: dict[int, list[tuple[int, int]]] | None = None
    portal: tp.Portal | None = None  # gets set by plugin
    ourVersionString: bytes = CowrieConfig.get(
        "ssh", "version", fallback="SSH-2.0-OpenSSH_6.0p1 Debian-4+deb7u2"
    ).encode("ascii")
    ssh_server_versions: list = [
    'SSH-2.0-5.1 F-Secure SSH Windows NT Server',
    'SSH-2.0-ReflectionForSecureIT_7.2.1',
    'SSH-2.0-4.3 SSH Secure Shell Tru64 UNIX',
    'SSH-2.0-OpenSSH_8.0p1 Debian-9+deb9u3',
    'SSH-2.0-OpenSSH_7.5 FreeBSD-11',
    'SSH-2.0-OpenSSH_6.7 Mikrotik_v6.43.12',
    'SSH-2.0-Cisco-1.25',
    'SSH-2.0-CiscoIOS_12.2XA',
    'SSH-2.0-8.47 sshlib: WinSSHD 6.32',
    'SSH-2.0-HUAWEI-VRP5.150',
    'SSH-2.0-FortiOS',
    'SSH-2.0-OpenSSH_3.6p1',
    'SSH-2.0-NetScreen',
    'SSH-2.0-ROSSSH',
    'SSH-2.0-Nortel',
    'SSH-2.0-Data ONTAP SSH v9.1P5',
    'SSH-2.0-Axway.Gateway',
    'SSH-2.0-HP Integrated Lights-Out mpSSH v1.1',
    'SSH-2.0-Comware-5.20',
    'SSH-1.5-SSH.0.1',
    'SSH-2.0-dropbear_2019.78',
    'SSH-2.0-Adtran_18.03',
    'SSH-2.0-McAfee Web Gateway SSH',
    'SSH-2.0-OpenSSH_8.1p1 Raspbian-5',
    'SSH-2.0-OpenSSH_7.6 Ubuntu-4ubuntu0.3',
    'SSH-2.0-OpenSSH_6.9 FreeBSD-10.2'
    ]


    def __init__(self, backend, pool_handler):
        self.pool_handler = pool_handler
        self.backend: str = backend
        self.privateKeys = {}
        self.publicKeys = {}
        self.services = {
            b"ssh-userauth": ProxySSHAuthServer
            if self.backend == "proxy"
            else HoneyPotSSHUserAuthServer,
            b"ssh-connection": connection.CowrieSSHConnection,
        }
        super().__init__()

    def logDispatch(self, **args):
        """
        Special delivery to the loggers to avoid scope problems
        """
        args["sessionno"] = "S{}".format(args["sessionno"])
        for output in self.tac.output_plugins:
            output.logDispatch(**args)

    def startFactory(self) -> None:
        # For use by the uptime command
        self.starttime = time.time()

        # Load/create keys
        try:
            public_key_auth = [
                i.encode("utf-8")
                for i in CowrieConfig.get("ssh", "public_key_auth").split(",")
            ]
        except NoOptionError:
            # no keys defined, use the three most common pub keys of OpenSSH
            public_key_auth = [b"ssh-rsa", b"ecdsa-sha2-nistp256", b"ssh-ed25519"]
        for key in public_key_auth:
            if key == b"ssh-rsa":
                rsaPubKeyString, rsaPrivKeyString = cowriekeys.getRSAKeys()
                self.publicKeys[key] = keys.Key.fromString(data=rsaPubKeyString)
                self.privateKeys[key] = keys.Key.fromString(data=rsaPrivKeyString)
            elif key == b"ssh-dss":
                dsaaPubKeyString, dsaPrivKeyString = cowriekeys.getDSAKeys()
                self.publicKeys[key] = keys.Key.fromString(data=dsaaPubKeyString)
                self.privateKeys[key] = keys.Key.fromString(data=dsaPrivKeyString)
            elif key == b"ecdsa-sha2-nistp256":
                ecdsaPuKeyString, ecdsaPrivKeyString = cowriekeys.getECDSAKeys()
                self.publicKeys[key] = keys.Key.fromString(data=ecdsaPuKeyString)
                self.privateKeys[key] = keys.Key.fromString(data=ecdsaPrivKeyString)
            elif key == b"ssh-ed25519":
                ed25519PubKeyString, ed25519PrivKeyString = cowriekeys.geted25519Keys()
                self.publicKeys[key] = keys.Key.fromString(data=ed25519PubKeyString)
                self.privateKeys[key] = keys.Key.fromString(data=ed25519PrivKeyString)

        _modulis = "/etc/ssh/moduli", "/private/etc/moduli"
        for _moduli in _modulis:
            try:
                self.primes = primes.parseModuliFile(_moduli)
                break
            except OSError:
                pass

        # this can come from backend in the future, check HonSSH's slim client
        self.ourVersionString = CowrieConfig.get(
            "ssh", "version", fallback="SSH-2.0-OpenSSH_6.0p1 Debian-4+deb7u2"
        ).encode("ascii")

        factory.SSHFactory.startFactory(self)
        log.msg("Ready to accept SSH connections")

    def stopFactory(self) -> None:
        factory.SSHFactory.stopFactory(self)

    def buildProtocol(self, addr):
        """
        Create an instance of the server side of the SSH protocol.

        @type addr: L{twisted.internet.interfaces.IAddress} provider
        @param addr: The address at which the server will listen.

        @rtype: L{cowrie.ssh.transport.HoneyPotSSHTransport}
        @return: The built transport.
        """
        t: transport.SSHServerTransport
        if self.backend == "proxy":
            t = proxyTransport.FrontendSSHTransport()
        else:
            t = shellTransport.HoneyPotSSHTransport()

        t.ourVersionString = random.choice(self.ssh_server_versions).encode("ascii")
        t.supportedPublicKeys = list(self.privateKeys.keys())

        if not self.primes:
            ske = t.supportedKeyExchanges[:]
            if b"diffie-hellman-group-exchange-sha1" in ske:
                ske.remove(b"diffie-hellman-group-exchange-sha1")
                log.msg("No moduli, no diffie-hellman-group-exchange-sha1")
            if b"diffie-hellman-group-exchange-sha256" in ske:
                ske.remove(b"diffie-hellman-group-exchange-sha256")
                log.msg("No moduli, no diffie-hellman-group-exchange-sha256")
            t.supportedKeyExchanges = ske

        try:
            t.supportedCiphers = [
                i.encode("utf-8") for i in CowrieConfig.get("ssh", "ciphers").split(",")
            ]
        except NoOptionError:
            # Reorder supported ciphers to resemble current openssh more
            t.supportedCiphers = [
                b"aes128-ctr",
                b"aes192-ctr",
                b"aes256-ctr",
                b"aes256-cbc",
                b"aes192-cbc",
                b"aes128-cbc",
                b"3des-cbc",
                b"blowfish-cbc",
                b"cast128-cbc",
            ]

        try:
            t.supportedMACs = [
                i.encode("utf-8") for i in CowrieConfig.get("ssh", "macs").split(",")
            ]
        except NoOptionError:
            # SHA1 and MD5 are considered insecure now. Use better algos
            # like SHA-256 and SHA-384
            t.supportedMACs = [
                b"hmac-sha2-512",
                b"hmac-sha2-384",
                b"hmac-sha2-256",
                b"hmac-sha1",
                b"hmac-md5",
            ]

        try:
            t.supportedCompressions = [
                i.encode("utf-8")
                for i in CowrieConfig.get("ssh", "compression").split(",")
            ]
        except NoOptionError:
            t.supportedCompressions = [b"zlib@openssh.com", b"zlib", b"none"]

        t.factory = self

        return t
