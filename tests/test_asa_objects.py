import pytest

# Set the path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from asa_objectified import NetworkObject
from asa_objectified import IcmpObject
from asa_objectified import TcpObject
from asa_objectified import UdpObject
from asa_objectified import ProtocolObject

def test_icmp_object_creation():
    i= IcmpObject(
        # name= "Stu",
        icmp_type='echo',
        icmp_code=40,
    )

    assert i.cli_full()== [
        'object service SVC_ICMP_TYPE_ECHO_CODE_40',
        ' service icmp echo 40',
        '!',
    ]

@pytest.mark.xfail
def test_xfail_incorrect_attributes():
    i= TcpObject(
        name= "Stu",
        icmp_type='echo',
        icmp_code=40,
    )
    i.cli_full()