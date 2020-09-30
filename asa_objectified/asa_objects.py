from ipaddress import IPv4Network
from ipaddress import IPv4Address
from enum import Enum
import ipaddress


class NetworkObject(object):
    """An ASA style network object. Can be a host, network, FQDN,
    or range object.
    """

    class ObjectType(Enum):
        RANGE = 1
        HOST = 2
        NETWORK = 3
        FQDN = 4

    def __init__(
        self,
        ob_type=None,
        ip=None,
        netmask=None,
        description=None,
        CIDR=None,
        name=None,
        fqdn=None,
        end_ip=None,  # End IP for a range
    ):
        self.description = description
        self.name = name
        self.type = ob_type

        # Initialize the object
        if not self.type:
            pass
        elif self.type in (NetworkObject.ObjectType.HOST,
                           NetworkObject.ObjectType.NETWORK):
            self.init_host_or_net_object(ip, netmask, CIDR)
        elif self.type == NetworkObject.ObjectType.RANGE:
            self.init_range_object(ip, end_ip)

        elif self.type == NetworkObject.ObjectType.FQDN:
            self.init_fqdn_object(fqdn)

    def init_fqdn_object(self, fqdn):
        """Sets the fqdn, name, and object type parameters for a
        FQDN-type object.
        """
        self.fqdn = fqdn
        self.type = NetworkObject.ObjectType.FQDN
        if not self.name:
            self.generate_name()

    def init_range_object(self, ip, end_ip):
        """Sets the start and end addresses for a range-type
        object, as well as the object-type and name.

        Args:
            ip (str): The starting address for the range
            end_ip (str): The ending address for the range
        """
        self.ip = IPv4Network(ip)
        self.end_ip = IPv4Network(end_ip)
        self.type = NetworkObject.ObjectType.RANGE
        if not self.name:
            self.generate_name()

    def init_host_or_net_object(self,
                                ip,
                                netmask=None,
                                CIDR=None,
                                ):
        """Sets the ip, name, and object type parameters for
        a Host or Network type object.

        Args:
            ip (str): The IP of the object, expressed as a string.
                Can be a single IP, or a network address with either
                CIDR or netmask notation. (10.1.1.0/255.255.255.0)
            netmask (str, optional): If ip is a single IP address, this
                can be used to manually specify a netmask to generate a
                network object. Defaults to None.
            CIDR (str, optional): Similar to netmask, this can be used to 
                specify a CIDR value in generating a network type object. 
                Defaults to None.
        """
        # Convert the supplied variables into an object
        if netmask:
            ip = IPv4Network(f'{ip}/{netmask}')
        elif CIDR:
            ip = IPv4Network(f'{ip}/{CIDR}')
        else:
            ip = IPv4Network(ip)

        self.ip = ip

        # Check if it's a /32
        if ip.prefixlen == 32:
            self.type = NetworkObject.ObjectType.HOST
        else:
            self.type = NetworkObject.ObjectType.NETWORK

        # Set the object name
        if not self.name:
            self.generate_name()

        return self.ip

    def generate_name(self) -> str:
        """Generates an object name based on the current attributes
        of the object.

        Raises:
            ValueError: Raised when NetworkObject not set to type

        Returns:
            str: The generated object name
        """

        if self.type == NetworkObject.ObjectType.HOST:
            self.name = f'HOST_{self.ip.network_address}'
        elif self.type == NetworkObject.ObjectType.NETWORK:
            self.name = f'NET_{self.ip.network_address}_{self.ip.prefixlen}'
        elif self.type == NetworkObject.ObjectType.RANGE:
            self.name = f'RANGE_{self.ip.network_address}-{self.end_ip.network_address}'
        elif self.type == NetworkObject.ObjectType.FQDN:
            self.name = f'FQDN_{self.fqdn}'
        else:
            raise ValueError(
                'NetworkObject not set to type when generating name.')

        return self.name

    def cli_definition(self) -> str:
        """Returns the single line CLI command which creates the object.
        """
        if not self.name:
            self.generate_name()
        return f'object network {self.name}'

    def cli_attributes(self) -> str:
        """Generates the CLI line which specifies the attributes of the 
        network object (as opposed to the first CLI line, which specifies 
        the name of the object).

        Raises:
            ValueError: If the object type is incorrectly set.

        Returns:
            str: The CLI commands
        """

        # Object details
        if not self.type:
            raise ValueError('No value set for object type.')

        elif self.type == NetworkObject.ObjectType.HOST:
            return f' host {self.ip.network_address}'

        elif self.type == NetworkObject.ObjectType.NETWORK:
            return f' subnet {self.ip.network_address} {self.ip.netmask}'

        elif self.type == NetworkObject.ObjectType.RANGE:
            return f' range {self.ip.network_address} {self.end_ip.network_address}'

        elif self.type == NetworkObject.ObjectType.FQDN:
            return f' fqdn {self.fqdn}'

        else:
            raise ValueError('Invalid value set for object type.')

    def cli_full(self) -> list:
        """Create the ASA-style CLI commands to create this 
        network object.

        Returns:
            list: A list of strings containing the CLI commands to create
                this object.
        """

        # Definition and attributes
        rule_text = [self.cli_definition, self.cli_attributes]

        # Optional description
        if self.description:
            rule_text.append(' description ' + self.description)

        rule_text.append('!')

        return rule_text

    def __str__(self):
        try:
            return '\n'.join(self.cli_full)
        except Exception:
            return "Unconfigured Network Object"

    @property
    def netmask(self):
        """Returns the netmask of the object.
        """
        return self.ip.netmask


class _ServiceObject(object):

    def __init__(self):
        pass

    # Object types
    class PortSelecterType(Enum):
        SINGLE = 'eq'
        RANGE = 'range'
        LESS_THAN = 'lt'
        GREATER_THAN = 'gt'
        NOT_EQUALS = 'neq'

    def generate_name(self) -> str:
        """Generates an object name based on the current attributes
        of the object.

        Returns:
            str: The generated object name
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Returns the object name, or sets it if no name was 
        previously assigned.

        Returns:
            str: The name of the object.
        """
        if self._name:
            return self._name
        else:
            return self.generate_name()

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def port_selecter_type(self) -> PortSelecterType:
        return self._port_selecter_type

    @port_selecter_type.setter
    def port_selecter_type(self, value: PortSelecterType):
        assert value in self.PortSelecterType, "Type is not valid"
        self._port_selecter_type = value

    def cli_definition(self) -> str:
        """Returns the single line CLI command which creates the object.
        """
        # Sets the name if no name exists yet
        if not self.name:
            self.generate_name()
        return f'object service {self.name}'

    def cli_attributes(self) -> str:
        """Generates the CLI line which specifies the attributes of the 
        service object (as opposed to the first CLI line, which specifies 
        the name of the object).

        Returns:
            str: The CLI commands
        """
        raise NotImplementedError

    def cli_full(self) -> list:
        """Generates the full set of CLI commands to create and define
        the object.

        Returns:
            list: A list of strings which can be sent to the device to 
                generate the object
        """
        return [self.cli_definition(), self.cli_attributes(), '!']


class _TcpOrUdpObject(_ServiceObject):
    """A class representing Cisco ASA-style TCP or UDP objects. 
    This class is not designed to be called directly. It must be 
    inherited by the TcpObject or UdpObject classes.
    """

    def __init__(self,
                 source_port_selecter_type=None,
                 source_port=None,  # Single port, or start port in range
                 source_end_port=None,  # End port in range
                 dest_port_selecter_type=None,
                 dest_port=None,
                 dest_end_port=None,
                 name=None,
                 ):
        self.name = name
        self.source_port_selecter_type = source_port_selecter_type
        self.source_port = source_port  # Single port, or start port in range
        self.source_end_port = source_end_port  # End port in range
        self.dest_port_selecter_type = dest_port_selecter_type
        self.dest_port = dest_port
        self.dest_end_port = dest_end_port

    def _check_port(self, port: int) -> bool:
        """Verifies that a port is a valid value

        Args:
            port (int): The port to check

        Raises:
            ValueError: If a value is not within 0 to 65535

        Returns:
            Bool: True if the value is a valid port
        """

        if port == None:
            return False
        elif not (0 <= int(port) <= 65535):
            raise ValueError('Port value is out of range')
        else:
            return True

    def generate_name(self) -> str:
        """Generates an object name based on the current attributes
        of the object.

        Returns:
            str: The generated object name
        """
        name = f'SVC_{self._OBJECT_TYPE.upper()}'
        if self.source_port_selecter_type == None:
            pass
        elif self.source_port_selecter_type == self.PortSelecterType.RANGE:
            name += f'_SRC_RANGE_{self.source_port}-{self.source_end_port}'
        else:
            name += f'_SRC_{self.source_port_selecter_type.value.upper()}_{self.source_port}'

        if self.dest_port_selecter_type == None:
            pass
        elif self.dest_port_selecter_type == self.PortSelecterType.RANGE:
            name += f'_DEST_RANGE_{self.dest_port}-{self.dest_end_port}'
        else:
            name += f'_DEST_{self.dest_port_selecter_type.value.upper()}_{self.dest_port}'

        self._name = name
        return name

    # Set the source port with some basic error checking
    @property
    def source_port(self):
        return self._source_port

    @source_port.setter
    def source_port(self, port: int):
        self._check_port(port)
        self._source_port = port

    # Set the source end port with some basic error checking
    @property
    def source_end_port(self):
        return self._source_end_port

    @source_end_port.setter
    def source_end_port(self, port: int):
        self._check_port(port)
        self._source_end_port = port

    # Set the destination port with some basic error checking
    @property
    def dest_port(self):
        return self._dest_port

    @dest_port.setter
    def dest_port(self, port: int):
        self._check_port(port)
        self._dest_port = port

    # Set the destination end port with some basic error checking
    @property
    def dest_end_port(self):
        return self._dest_end_port

    @dest_port.setter
    def dest_end_port(self, port: int):
        self._check_port(port)
        self._dest_end_port = port

    def cli_attributes(self) -> str:
        """Generates the CLI line which specifies the attributes of the 
        service object (as opposed to the first CLI line, which specifies 
        the name of the object).

        Returns:
            str: The CLI commands
        """

        # Error checking to make sure the port selector types are valid
        assert ((not self.source_port_selecter_type) or
                (self.source_port_selecter_type in _ServiceObject.PortSelecterType))
        assert ((not self.dest_port_selecter_type) or
                (self.dest_port_selecter_type in _ServiceObject.PortSelecterType))

        # Check errors and set the source attribute
        if not self.source_port_selecter_type:
            source = ''
        elif self.source_port_selecter_type == _ServiceObject.PortSelecterType.RANGE:
            assert self.source_port and self.source_end_port, 'Range starting or ending port not defined'
            source = f' source {self.source_port_selecter_type.value} {self.source_port} {self.source_end_port}'
        else:
            assert self.source_port, 'Source port not defined'
            source = f' source {self.source_port_selecter_type.value} {self.source_port}'

        # Check errors and set the destination string
        if not self.dest_port_selecter_type:
            dest = ''
        elif self.dest_port_selecter_type == _ServiceObject.PortSelecterType.RANGE:
            assert self.dest_port and self.dest_end_port, 'Range starting or ending port not defined'
            dest = f' source {self.dest_port_selecter_type.value} {self.dest_port} {self.dest_end_port}'
        else:
            assert self.dest_port, 'Destination port not defined'
            dest = f' destination {self.dest_port_selecter_type.value} {self.dest_port}'

        return f'service {self._OBJECT_TYPE}{source}{dest}'


class TcpObject(_TcpOrUdpObject):
    _OBJECT_TYPE = 'tcp'


class UdpObject(_TcpOrUdpObject):
    _OBJECT_TYPE = 'udp'


class IcmpObject(_ServiceObject):
    """This class represents an ASA-style ICMP service object. It
    contains methods to define the attributes of the object, as well
    as render the object into CLI commands which can be sent to an asa 
    device.
    """

    def __init__(self,
                 name=None,
                 icmp_type=None,
                 icmp_code=None,
                 ):
        self.name = name
        self.icmp_code = icmp_code
        self.icmp_type = icmp_type

    def generate_name(self) -> str:
        """Generates an object name based on the current attributes
        of the object.

        Returns:
            str: The generated object name
        """
        assert self.icmp_type, 'ICMP type attribute unset during name generation'
        name = f'SVC_ICMP_TYPE_{self.icmp_type}'

        if self.icmp_code:
            name += '_CODE_' + str(self.icmp_code)

        self.name = name.upper()
        return self.name

    @property
    def icmp_code(self) -> int:
        return self._icmp_code

    @icmp_code.setter
    def icmp_code(self, value: int):
        """Verifies that a given ICMP code is between 1 and 255, then
        sets the internal variable.

        Args:
            value (int): The ICMP code to validate. Also accepts
                None.
        """
        # Permit this value to be unset.
        if value == None:
            self._icmp_code = None
            return True

        if self._verify_icmp_code(value):
            self._icmp_code = value
            return True
        else:
            return False

    @property
    def icmp_type(self) -> str:
        return self._icmp_type

    @icmp_type.setter
    def icmp_type(self, value: any):
        """Verifies that a given ICMP type is either a str or an int
        between 0 and 255, then sets the internal variable.

        Args:
            value (any): The ICMP type to validate, either as a str or int.
                Also accepts None.

        Raises:
            ValueError: If the code is invalid.
        """
        # Permit this value to be unset.
        if value == None:
            self._icmp_type = None
            return True

        if self._verify_icmp_type(value):
            self._icmp_type = value
            return True
        else:
            return False

    def _verify_icmp_code(self,
                          value: int,
                          raise_error: bool = True
                          ) -> bool:
        """Verifies that a given ICMP code is between 1 and 255.

        Args:
            value (int): The ICMP code to validate.
            raise_error (bool): Raises error on failed validation if True.

        Raises:
            ValueError: If the code is invalid.

        Returns:
            bool: True if the ICMP code is valid.
        """

        if (1 <= int(value) <= 255):
            return True
        else:
            if raise_error:
                raise ValueError('The given ICMP code is invalid')
            return False

    def _verify_icmp_type(self,
                          value: any,
                          raise_error: bool = True
                          ) -> bool:
        """Verifies that a given ICMP type is either a str or an int
        between 0 and 255.

        Args:
            value (any): The ICMP type to validate, either as a str or int.
            raise_error (bool): Raises error on failed validation if True.

        Raises:
            ValueError: If the code is invalid.

        Returns:
            bool: True if the ICMP type is valid.
        """
        # Check if it is a string. Really we should verify this against all
        # possible ICMP type values, but I don't have that list right now.
        if (isinstance(value, str) and not value.isnumeric()):
            return True

        # Check to make sure the type was set at all
        elif (not value):
            raise ValueError('ICMP Type not set')

        # Verify that it is a value between 0 and 255
        if (0 <= int(value) <= 255):
            return True
        else:
            if raise_error:
                raise ValueError('The given ICMP type is invalid')
            return False

    def cli_definition(self):
        return super().cli_definition()

    def cli_attributes(self) -> str:
        """Generates the CLI line which specifies the attributes of the 
        service object (as opposed to the first CLI line, which specifies 
        the name of the object).

        Returns:
            str: The CLI command
        """
        self._verify_icmp_type(self.icmp_type)
        self._verify_icmp_code(self._icmp_code)

        c = f' service icmp {self.icmp_type}'
        if self.icmp_code:
            c += ' ' + str(self.icmp_code)

        return c

    def cli_full(self):
        return super().cli_full()


class ProtocolObject(_ServiceObject):
    def __init__(self):
        raise NotImplementedError


# i= TcpObject(
#     name= "Stu",
#     icmp_type='echo',
#     icmp_code=40,
# )

# print('\n'.join(i.cli_full()))
