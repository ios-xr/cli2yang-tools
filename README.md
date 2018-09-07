# cli2yang-tools
Simple tools to convert existing CLI to YANG formats (XML, JSON)

## cli2xmljson.py
The purpose of the script cli2xmljson.py is to be able to convert any existing CLI configuration on an IOS-XR router (tested on release >6.4.1)
to an equivalent YANG-Based XML rendering for use over netconf and YANG-Based JSON rendering for use over gRPC.

### Clone the Repo
Clone the git repo with `--recursive` to make sure the  submodule bigmuddy-network-telemetry-proto/ is also pulled in:

```
admin@devbox:~$ git clone --recursive https://github.com/ios-xr/cli2yang-tools
Cloning into 'cli2yang-tools'...
remote: Counting objects: 432, done.
remote: Compressing objects: 100% (198/198), done.
remote: Total 432 (delta 192), reused 428 (delta 188), pack-reused 0
Receiving objects: 100% (432/432), 86.89 KiB | 0 bytes/s, done.
Resolving deltas: 100% (192/192), done.
Checking connectivity... done.
Submodule 'iosxr_grpc/bigmuddy-network-telemetry-proto' (https://github.com/cisco/bigmuddy-network-telemetry-proto) registered for path 'iosxr_grpc/bigmuddy-network-telemetry-proto'
Cloning into 'iosxr_grpc/bigmuddy-network-telemetry-proto'...
remote: Counting objects: 24542, done.
remote: Total 24542 (delta 0), reused 0 (delta 0), pack-reused 24542
Receiving objects: 100% (24542/24542), 6.06 MiB | 3.18 MiB/s, done.
Resolving deltas: 100% (8324/8324), done.
Checking connectivity... done.
Submodule path 'iosxr_grpc/bigmuddy-network-telemetry-proto': checked out '4419cd20fb73f05d059a37fa3e41fe55f02a528f'
admin@devbox:~$ cd cli2yang-tools/


```


### Install dependencies and generate bindings
The build script has been created for use with Ubuntu 16.04+. Take a look at the script to modify it for other distributions.
Run the script `build_dependencies.sh`. This should install all the dependencies (ncclient, xmltodict, lxml, grpcio etc.) and build the python bindings from the mdt_grpc_dialin.proto and telemetry.proto file provided by `bigmuddy-network-telemetry-proto`.

```
admin@devbox:cli2yang-tools$ sudo ./build_dependencies.sh 
Hit:1 http://ppa.launchpad.net/ansible/ansible/ubuntu xenial InRelease
Hit:2 http://security.ubuntu.com/ubuntu xenial-security InRelease                                                                    
Hit:3 https://download.docker.com/linux/ubuntu xenial InRelease
Hit:4 http://us.archive.ubuntu.com/ubuntu xenial InRelease
Hit:5 http://us.archive.ubuntu.com/ubuntu xenial-updates InRelease
Hit:6 http://us.archive.ubuntu.com/ubuntu xenial-backports InRelease
Reading package lists... Done                     
Reading package lists... Done
Building dependency tree       
Reading state information... Done


..................................# OUTPUT SNIPPED #.............................................

Generating Python bindings...+ python -m grpc_tools.protoc -I ./ --python_out=/home/admin/cli2yang-tools/iosxr_grpc/genpy --grpc_python_out=/home/admin/cli2yang-tools/iosxr_grpc/genpy ./mdt_grpc_dialin/mdt_grpc_dialin.proto
+ mkdir -p /home/admin/cli2yang-tools/iosxr_grpc/genpy/./mdt_grpc_dialin
+ touch /home/admin/cli2yang-tools/iosxr_grpc/genpy/./mdt_grpc_dialin/__init__.py
+ 2to3 -w '/home/admin/cli2yang-tools/iosxr_grpc/genpy/*.py'
+ set +x
+ python -m grpc_tools.protoc -I ./ --python_out=/home/admin/cli2yang-tools/iosxr_grpc/genpy --grpc_python_out=/home/admin/cli2yang-tools/iosxr_grpc/genpy telemetry.proto
+ 2to3 -w /home/admin/cli2yang-tools/iosxr_grpc/genpy/telemetry_pb2_grpc.py /home/admin/cli2yang-tools/iosxr_grpc/genpy/telemetry_pb2.py
+ touch /home/admin/cli2yang-tools/iosxr_grpc/genpy/__init__.py
+ set +x
Done
admin@devbox:cli2yang-tools$ 


```

### Configure your router

Put whatever configuration (through CLI) that you want to put on your router. Make sure you enable netconf over SSH and gRPC as part of the configuration.

For example, the following CLI configuration was applied to the router under test:

```
!! IOS XR Configuration version = 6.4.1
!! Last configuration change at Fri Sep  7 01:27:21 2018 by admin
!
hostname r1
banner motd ;
--------------------------------------------------------------------------
  Router 1 (Cisco IOS XR Sandbox)
--------------------------------------------------------------------------
;
logging console debugging
service timestamps log datetime msec
service timestamps debug datetime msec
username admin
 group root-lr
 group cisco-support
 secret 5 $1$A4C9$oaNorr6BXDruE4gDd086L.
!
line console
 timestamp disable
 exec-timeout 0 0
!
vty-pool default 0 4 line-template VTY-TEMPLATE
call-home
 service active
 contact smart-licensing
 profile CiscoTAC-1
  active
  destination transport-method http
 !
!
interface MgmtEth0/RP0/CPU0/0
 description *** MANAGEMENT INTERFACE ***
 ipv4 address dhcp
!
interface GigabitEthernet0/0/0/0
 ipv6 address 1010:1010::10/64
 ipv6 enable
!
interface GigabitEthernet0/0/0/1
 ipv6 address 2020:2020::10/64
 ipv6 enable
!
interface GigabitEthernet0/0/0/2
 shutdown
!
interface GigabitEthernet0/0/0/3
 shutdown
!
interface GigabitEthernet0/0/0/4
 shutdown
!
router static
 address-family ipv4 unicast
  0.0.0.0/0 10.0.2.2
  1.2.3.5/32 10.0.2.2
 !
!
router bgp 65400
 bgp router-id 11.1.1.10
 address-family ipv4 unicast
  network 11.1.1.0/24
 !
 neighbor 11.1.1.20
  remote-as 65450
  address-family ipv4 unicast
   next-hop-self
  !
 !
!
grpc
 port 57777
 no-tls
 service-layer
 !
!
telemetry model-driven
 destination-group DGroup1
  address-family ipv4 192.168.122.11 port 5432
   encoding self-describing-gpb
   protocol tcp
  !
 !
 sensor-group SGroup1
  sensor-path Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters
 !
 sensor-group IPV6Neighbor
  sensor-path Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address
 !
 subscription IPV6
  sensor-group-id IPV6Neighbor sample-interval 15000
 !
 subscription Sub1
  sensor-group-id SGroup1 sample-interval 30000
  destination-id DGroup1
 !
!
netconf-yang agent
 ssh
!
ssh server v2
ssh server netconf vrf default
end




```

Now the goal is to convert this CLI into corresponding XML and JSON [(RFC7591)]()


