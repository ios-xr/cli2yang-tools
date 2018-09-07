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

Now the goal is to convert this CLI into corresponding XML [(RFC7950)](https://tools.ietf.org/html/rfc7950) and JSON [(RFC7951)](https://tools.ietf.org/html/rfc7951) based on the Yang models supported by the router.

### Run the script

Run the script against the router. Before starting, dump the options available:

```
admin@devbox:cli2yang-tools$ ./cli2xmljson.py 
usage: cli2xmljson.py [-h] [-s HOST] [-n NC_PORT] [-g GRPC_PORT] [-u USERNAME]
                      [-p PASSWORD] [-d] [-t] [-x NC_XML_FILE]
                      [-j GRPC_JSON_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --server HOST
                        IP address of netconf server and gRPC server on the
                        router
  -n NC_PORT, --netconf-port NC_PORT
                        netconf port
  -g GRPC_PORT, --grpc-port GRPC_PORT
                        gRPC port
  -u USERNAME, --username USERNAME
                        IOS-XR AAA username
  -p PASSWORD, --password PASSWORD
                        IOS-XR AAA password
  -d, --debug           Enable debugging
  -t, --test-merge      Test config merge with each output file
  -x NC_XML_FILE, --nc-xml-file NC_XML_FILE
                        Specify output file path for netconf based XML output
  -j GRPC_JSON_FILE, --grpc-json-file GRPC_JSON_FILE
                        Specify output file path for gRPC based JSON output
admin@devbox:cli2yang-tools$ 


```

For the router configured with netconf and gRPC as shown above, run the script like so:
(you can specify custom filenames using options -x and -j: The default filenames are `./yang_nc.xml` for the XML representation and `./yang_grpc.json` for the JSON representation).


```

admin@devbox:cli2yang-tools$ 
admin@devbox:cli2yang-tools$ python3 ./cli2xmljson.py -s 192.168.122.21 -n 830 -g 57777 -u admin -p admin 
Router's CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Router's CLI configuration converted into YANG JSON and saved in file: ./yang_grpc.json
admin@devbox:cli2yang-tools$ 



```

### Verify the files created

The XML file created by the script ends up looking something like:  

(Use this file to directly do a config-merge/config-replace over netconf).


```xml
admin@devbox:cli2yang-tools$ cat yang_nc.xml 
<?xml version="1.0" encoding="utf-8"?>
<config>
	<host-names xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-shellutil-cfg">
		<host-name>r1</host-name>
	</host-names>
	<call-home xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-call-home-cfg">
		<active></active>
		<contact-smart-licensing>true</contact-smart-licensing>
		<profiles>
			<profile>
				<profile-name>CiscoTAC-1</profile-name>
				<create></create>
				<active></active>
				<methods>
					<method>
						<method>email</method>
						<enable>false</enable>
					</method>
					<method>
						<method>http</method>
						<enable>true</enable>
					</method>
				</methods>
			</profile>
		</profiles>
	</call-home>
	<telemetry-model-driven xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-telemetry-model-driven-cfg">
		<destination-groups>
			<destination-group>
				<destination-id>DGroup1</destination-id>
				<ipv4-destinations>
					<ipv4-destination>
						<ipv4-address>192.168.122.11</ipv4-address>
						<destination-port>5432</destination-port>
						<encoding>self-describing-gpb</encoding>
						<protocol>
							<protocol>tcp</protocol>
							<no-tls>1</no-tls>
						</protocol>
					</ipv4-destination>
				</ipv4-destinations>
			</destination-group>
		</destination-groups>
		<sensor-groups>
			<sensor-group>
				<sensor-group-identifier>SGroup1</sensor-group-identifier>
				<sensor-paths>
					<sensor-path>
						<telemetry-sensor-path>Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters</telemetry-sensor-path>
					</sensor-path>
				</sensor-paths>
			</sensor-group>
			<sensor-group>
				<sensor-group-identifier>IPV6Neighbor</sensor-group-identifier>
				<sensor-paths>
					<sensor-path>
						<telemetry-sensor-path>Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address</telemetry-sensor-path>
					</sensor-path>
				</sensor-paths>
			</sensor-group>
		</sensor-groups>
		<enable></enable>
		<subscriptions>
			<subscription>
				<subscription-identifier>IPV6</subscription-identifier>
				<sensor-profiles>
					<sensor-profile>
						<sensorgroupid>IPV6Neighbor</sensorgroupid>
						<sample-interval>15000</sample-interval>
					</sensor-profile>
				</sensor-profiles>
			</subscription>
			<subscription>
				<subscription-identifier>Sub1</subscription-identifier>
				<sensor-profiles>
					<sensor-profile>
						<sensorgroupid>SGroup1</sensorgroupid>
						<sample-interval>30000</sample-interval>
					</sensor-profile>
				</sensor-profiles>
				<destination-profiles>
					<destination-profile>
						<destination-id>DGroup1</destination-id>
					</destination-profile>
				</destination-profiles>
			</subscription>
		</subscriptions>
	</telemetry-model-driven>
	<interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
		<interface-configuration>
			<active>act</active>
			<interface-name>MgmtEth0/RP0/CPU0/0</interface-name>
			<description>*** MANAGEMENT INTERFACE ***</description>
			<ipv4-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg">
				<addresses>
					<dhcp>
						<enabled></enabled>
						<pattern>MgmtEth0_RP0_CPU0_0</pattern>
					</dhcp>
				</addresses>
			</ipv4-network>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>GigabitEthernet0/0/0/0</interface-name>
			<ipv6-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv6-ma-cfg">
				<addresses>
					<regular-addresses>
						<regular-address>
							<address>1010:1010::10</address>
							<prefix-length>64</prefix-length>
							<zone>0</zone>
						</regular-address>
					</regular-addresses>
					<auto-configuration>
						<enable></enable>
					</auto-configuration>
				</addresses>
			</ipv6-network>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>GigabitEthernet0/0/0/1</interface-name>
			<ipv6-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv6-ma-cfg">
				<addresses>
					<regular-addresses>
						<regular-address>
							<address>2020:2020::10</address>
							<prefix-length>64</prefix-length>
							<zone>0</zone>
						</regular-address>
					</regular-addresses>
					<auto-configuration>
						<enable></enable>
					</auto-configuration>
				</addresses>
			</ipv6-network>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>GigabitEthernet0/0/0/2</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>GigabitEthernet0/0/0/3</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>GigabitEthernet0/0/0/4</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
	</interface-configurations>
	<banners xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-infra-cfg">
		<banner>
			<banner-name>motd</banner-name>
			<banner-text>;
--------------------------------------------------------------------------
  Router 1 (Cisco IOS XR Sandbox)
--------------------------------------------------------------------------
;</banner-text>
		</banner>
	</banners>
	<aaa xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-lib-cfg">
		<usernames xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-locald-cfg">
			<username>
				<ordering-index>0</ordering-index>
				<name>admin</name>
				<usergroup-under-usernames>
					<usergroup-under-username>
						<name>root-lr</name>
					</usergroup-under-username>
					<usergroup-under-username>
						<name>cisco-support</name>
					</usergroup-under-username>
				</usergroup-under-usernames>
				<secret>$1$A4C9$oaNorr6BXDruE4gDd086L.</secret>
			</username>
		</usernames>
	</aaa>
	<grpc xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-man-ems-cfg">
		<port>57777</port>
		<no-tls></no-tls>
		<enable></enable>
		<service-layer>
			<enable></enable>
		</service-layer>
	</grpc>
	<vty xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-tty-vty-cfg">
		<vty-pools>
			<vty-pool>
				<pool-name>default</pool-name>
				<first-vty>0</first-vty>
				<last-vty>4</last-vty>
				<line-template>VTY-TEMPLATE</line-template>
			</vty-pool>
		</vty-pools>
	</vty>
	<ssh xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-crypto-ssh-cfg">
		<server>
			<v2></v2>
			<netconf-vrf-table>
				<vrf>
					<vrf-name>default</vrf-name>
					<enable></enable>
				</vrf>
			</netconf-vrf-table>
		</server>
	</ssh>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65400</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>11.1.1.10</router-id>
							<global-afs>
								<global-af>
									<af-name>ipv4-unicast</af-name>
									<enable></enable>
									<sourced-networks>
										<sourced-network>
											<network-addr>11.1.1.0</network-addr>
											<network-prefix>24</network-prefix>
										</sourced-network>
									</sourced-networks>
								</global-af>
							</global-afs>
						</global>
						<bgp-entity>
							<neighbors>
								<neighbor>
									<neighbor-address>11.1.1.20</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65450</as-yy>
									</remote-as>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
											<next-hop-self>true</next-hop-self>
										</neighbor-af>
									</neighbor-afs>
								</neighbor>
							</neighbors>
						</bgp-entity>
					</default-vrf>
				</four-byte-as>
			</instance-as>
		</instance>
	</bgp>
	<netconf-yang xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-man-netconf-cfg">
		<agent>
			<ssh>
				<enable></enable>
			</ssh>
		</agent>
	</netconf-yang>
	<tty xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-tty-server-cfg">
		<tty-lines>
			<tty-line>
				<name>console</name>
				<exec>
					<time-stamp>false</time-stamp>
					<timeout>
						<minutes>0</minutes>
						<seconds>0</seconds>
					</timeout>
				</exec>
			</tty-line>
		</tty-lines>
	</tty>
	<syslog-service xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-syslog-cfg">
		<timestamps>
			<log>
				<log-datetime>
					<log-datetime-value>
						<msec>enable</msec>
					</log-datetime-value>
				</log-datetime>
			</log>
			<debug>
				<debug-datetime>
					<datetime-value>
						<msec>enable</msec>
					</datetime-value>
				</debug-datetime>
			</debug>
		</timestamps>
	</syslog-service>
	<syslog xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-syslog-cfg">
		<console-logging>
			<logging-level>debug</logging-level>
		</console-logging>
	</syslog>
	<router-static xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ip-static-cfg">
		<default-vrf>
			<address-family>
				<vrfipv4>
					<vrf-unicast>
						<vrf-prefixes>
							<vrf-prefix>
								<prefix>0.0.0.0</prefix>
								<prefix-length>0</prefix-length>
								<vrf-route>
									<vrf-next-hop-table>
										<vrf-next-hop-next-hop-address>
											<next-hop-address>10.0.2.2</next-hop-address>
										</vrf-next-hop-next-hop-address>
									</vrf-next-hop-table>
								</vrf-route>
							</vrf-prefix>
							<vrf-prefix>
								<prefix>1.2.3.5</prefix>
								<prefix-length>32</prefix-length>
								<vrf-route>
									<vrf-next-hop-table>
										<vrf-next-hop-next-hop-address>
											<next-hop-address>10.0.2.2</next-hop-address>
										</vrf-next-hop-next-hop-address>
									</vrf-next-hop-table>
								</vrf-route>
							</vrf-prefix>
						</vrf-prefixes>
					</vrf-unicast>
				</vrfipv4>
			</address-family>
		</default-vrf>
	</router-static>
	<fpd xmlns="http://www.cisco.com/ns/yang/Cisco-IOS-XR-sysadmin-fpd-infra-cli-fpd">
		<config>
			<auto-upgrade>disable</auto-upgrade>
		</config>
	</fpd>
	<service xmlns="http://www.cisco.com/ns/yang/Cisco-IOS-XR-sysadmin-services">
		<cli>
			<interactive>
				<enabled>true</enabled>
			</interactive>
		</cli>
	</service>
	<telemetry-system xmlns="http://openconfig.net/yang/telemetry">
		<destination-groups>
			<destination-group>
				<group-id>DGroup1</group-id>
				<config>
					<group-id>DGroup1</group-id>
				</config>
				<destinations>
					<destination>
						<destination-address>192.168.122.11</destination-address>
						<destination-port>5432</destination-port>
						<config>
							<destination-address>192.168.122.11</destination-address>
							<destination-port>5432</destination-port>
							<destination-protocol>TCP</destination-protocol>
						</config>
					</destination>
				</destinations>
			</destination-group>
		</destination-groups>
		<sensor-groups>
			<sensor-group>
				<sensor-group-id>SGroup1</sensor-group-id>
				<config>
					<sensor-group-id>SGroup1</sensor-group-id>
				</config>
				<sensor-paths>
					<sensor-path>
						<path>Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters</path>
						<config>
							<path>Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters</path>
						</config>
					</sensor-path>
				</sensor-paths>
			</sensor-group>
			<sensor-group>
				<sensor-group-id>IPV6Neighbor</sensor-group-id>
				<config>
					<sensor-group-id>IPV6Neighbor</sensor-group-id>
				</config>
				<sensor-paths>
					<sensor-path>
						<path>Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address</path>
						<config>
							<path>Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address</path>
						</config>
					</sensor-path>
				</sensor-paths>
			</sensor-group>
		</sensor-groups>
		<subscriptions>
			<persistent>
				<subscription>
					<subscription-id>IPV6</subscription-id>
					<config>
						<subscription-id>IPV6</subscription-id>
					</config>
					<sensor-profiles>
						<sensor-profile>
							<sensor-group>IPV6Neighbor</sensor-group>
							<config>
								<sensor-group>IPV6Neighbor</sensor-group>
								<sample-interval>15000</sample-interval>
							</config>
						</sensor-profile>
					</sensor-profiles>
				</subscription>
				<subscription>
					<subscription-id>Sub1</subscription-id>
					<config>
						<subscription-id>Sub1</subscription-id>
					</config>
					<sensor-profiles>
						<sensor-profile>
							<sensor-group>SGroup1</sensor-group>
							<config>
								<sensor-group>SGroup1</sensor-group>
								<sample-interval>30000</sample-interval>
							</config>
						</sensor-profile>
					</sensor-profiles>
					<destination-groups>
						<destination-group>
							<group-id>DGroup1</group-id>
							<config>
								<group-id>DGroup1</group-id>
							</config>
						</destination-group>
					</destination-groups>
				</subscription>
			</persistent>
		</subscriptions>
	</telemetry-system>
	<interfaces xmlns="http://openconfig.net/yang/interfaces">
		<interface>
			<name>MgmtEth0/RP0/CPU0/0</name>
			<config>
				<name>MgmtEth0/RP0/CPU0/0</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:ethernetCsmacd</type>
				<enabled>true</enabled>
				<description>*** MANAGEMENT INTERFACE ***</description>
			</config>
			<ethernet xmlns="http://openconfig.net/yang/interfaces/ethernet">
				<config>
					<auto-negotiate>false</auto-negotiate>
				</config>
			</ethernet>
			<subinterfaces>
				<subinterface>
					<index>0</index>
				</subinterface>
			</subinterfaces>
		</interface>
		<interface>
			<name>GigabitEthernet0/0/0/0</name>
			<config>
				<name>GigabitEthernet0/0/0/0</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:ethernetCsmacd</type>
				<enabled>true</enabled>
			</config>
			<ethernet xmlns="http://openconfig.net/yang/interfaces/ethernet">
				<config>
					<auto-negotiate>false</auto-negotiate>
				</config>
			</ethernet>
			<subinterfaces>
				<subinterface>
					<index>0</index>
					<ipv6 xmlns="http://openconfig.net/yang/interfaces/ip">
						<addresses>
							<address>
								<ip>1010:1010::10</ip>
								<config>
									<ip>1010:1010::10</ip>
									<prefix-length>64</prefix-length>
								</config>
							</address>
						</addresses>
						<config>
							<enabled>true</enabled>
						</config>
					</ipv6>
				</subinterface>
			</subinterfaces>
		</interface>
		<interface>
			<name>GigabitEthernet0/0/0/1</name>
			<config>
				<name>GigabitEthernet0/0/0/1</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:ethernetCsmacd</type>
				<enabled>true</enabled>
			</config>
			<ethernet xmlns="http://openconfig.net/yang/interfaces/ethernet">
				<config>
					<auto-negotiate>false</auto-negotiate>
				</config>
			</ethernet>
			<subinterfaces>
				<subinterface>
					<index>0</index>
					<ipv6 xmlns="http://openconfig.net/yang/interfaces/ip">
						<addresses>
							<address>
								<ip>2020:2020::10</ip>
								<config>
									<ip>2020:2020::10</ip>
									<prefix-length>64</prefix-length>
								</config>
							</address>
						</addresses>
						<config>
							<enabled>true</enabled>
						</config>
					</ipv6>
				</subinterface>
			</subinterfaces>
		</interface>
		<interface>
			<name>GigabitEthernet0/0/0/2</name>
			<config>
				<name>GigabitEthernet0/0/0/2</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:ethernetCsmacd</type>
				<enabled>false</enabled>
			</config>
			<ethernet xmlns="http://openconfig.net/yang/interfaces/ethernet">
				<config>
					<auto-negotiate>false</auto-negotiate>
				</config>
			</ethernet>
		</interface>
		<interface>
			<name>GigabitEthernet0/0/0/3</name>
			<config>
				<name>GigabitEthernet0/0/0/3</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:ethernetCsmacd</type>
				<enabled>false</enabled>
			</config>
			<ethernet xmlns="http://openconfig.net/yang/interfaces/ethernet">
				<config>
					<auto-negotiate>false</auto-negotiate>
				</config>
			</ethernet>
		</interface>
		<interface>
			<name>GigabitEthernet0/0/0/4</name>
			<config>
				<name>GigabitEthernet0/0/0/4</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:ethernetCsmacd</type>
				<enabled>false</enabled>
			</config>
			<ethernet xmlns="http://openconfig.net/yang/interfaces/ethernet">
				<config>
					<auto-negotiate>false</auto-negotiate>
				</config>
			</ethernet>
		</interface>
	</interfaces>
	<lacp xmlns="http://openconfig.net/yang/lacp">
		<interfaces>
			<interface>
				<name>MgmtEth0/RP0/CPU0/0</name>
				<config>
					<name>MgmtEth0/RP0/CPU0/0</name>
				</config>
			</interface>
			<interface>
				<name>GigabitEthernet0/0/0/0</name>
				<config>
					<name>GigabitEthernet0/0/0/0</name>
				</config>
			</interface>
			<interface>
				<name>GigabitEthernet0/0/0/1</name>
				<config>
					<name>GigabitEthernet0/0/0/1</name>
				</config>
			</interface>
			<interface>
				<name>GigabitEthernet0/0/0/2</name>
				<config>
					<name>GigabitEthernet0/0/0/2</name>
				</config>
			</interface>
			<interface>
				<name>GigabitEthernet0/0/0/3</name>
				<config>
					<name>GigabitEthernet0/0/0/3</name>
				</config>
			</interface>
			<interface>
				<name>GigabitEthernet0/0/0/4</name>
				<config>
					<name>GigabitEthernet0/0/0/4</name>
				</config>
			</interface>
		</interfaces>
	</lacp>
	<network-instances xmlns="http://openconfig.net/yang/network-instance">
		<network-instance>
			<name>default</name>
			<protocols>
				<protocol>
					<identifier xmlns:idx="http://openconfig.net/yang/policy-types">idx:BGP</identifier>
					<name>default</name>
					<config>
						<identifier xmlns:idx="http://openconfig.net/yang/policy-types">idx:BGP</identifier>
						<name>default</name>
					</config>
					<bgp>
						<global>
							<config>
								<as>65400</as>
								<router-id>11.1.1.10</router-id>
							</config>
							<afi-safis>
								<afi-safi>
									<afi-safi-name>IPV4_UNICAST</afi-safi-name>
									<config>
										<afi-safi-name>IPV4_UNICAST</afi-safi-name>
										<enabled>true</enabled>
									</config>
								</afi-safi>
							</afi-safis>
						</global>
						<neighbors>
							<neighbor>
								<neighbor-address>11.1.1.20</neighbor-address>
								<config>
									<neighbor-address>11.1.1.20</neighbor-address>
									<peer-as>65450</peer-as>
								</config>
								<afi-safis>
									<afi-safi>
										<afi-safi-name>IPV4_UNICAST</afi-safi-name>
										<config>
											<afi-safi-name>IPV4_UNICAST</afi-safi-name>
											<enabled>true</enabled>
										</config>
									</afi-safi>
								</afi-safis>
							</neighbor>
						</neighbors>
					</bgp>
				</protocol>
				<protocol>
					<identifier xmlns:idx="http://openconfig.net/yang/policy-types">idx:STATIC</identifier>
					<name>DEFAULT</name>
					<config>
						<identifier xmlns:idx="http://openconfig.net/yang/policy-types">idx:STATIC</identifier>
						<name>DEFAULT</name>
					</config>
					<static-routes>
						<static>
							<prefix>0.0.0.0/0</prefix>
							<config>
								<prefix>0.0.0.0/0</prefix>
							</config>
							<next-hops>
								<next-hop>
									<index>**10.0.2.2**</index>
									<config>
										<index>**10.0.2.2**</index>
										<next-hop>10.0.2.2</next-hop>
									</config>
								</next-hop>
							</next-hops>
						</static>
						<static>
							<prefix>1.2.3.5/32</prefix>
							<config>
								<prefix>1.2.3.5/32</prefix>
							</config>
							<next-hops>
								<next-hop>
									<index>**10.0.2.2**</index>
									<config>
										<index>**10.0.2.2**</index>
										<next-hop>10.0.2.2</next-hop>
									</config>
								</next-hop>
							</next-hops>
						</static>
					</static-routes>
				</protocol>
			</protocols>
		</network-instance>
	</network-instances>
</config>


```


Similarly, the corresponding json file created is:  
(Use this file for configuration over gRPC)



```json
admin@devbox:cli2yang-tools$ cat yang_grpc.json 
{
    "Cisco-IOS-XR-tty-server-cfg:tty": {
        "tty-lines": {
            "tty-line": [
                {
                    "name": "console",
                    "exec": {
                        "timeout": {
                            "seconds": 0,
                            "minutes": 0
                        },
                        "time-stamp": false
                    }
                }
            ]
        }
    },
    "openconfig-network-instance:network-instances": {
        "network-instance": [
            {
                "name": "default",
                "protocols": {
                    "protocol": [
                        {
                            "name": "DEFAULT",
                            "config": {
                                "name": "DEFAULT",
                                "identifier": "openconfig-policy-types:STATIC"
                            },
                            "static-routes": {
                                "static": [
                                    {
                                        "config": {
                                            "prefix": "0.0.0.0/0"
                                        },
                                        "prefix": "0.0.0.0/0",
                                        "next-hops": {
                                            "next-hop": [
                                                {
                                                    "config": {
                                                        "next-hop": "10.0.2.2",
                                                        "index": "**10.0.2.2**"
                                                    },
                                                    "index": "**10.0.2.2**"
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "config": {
                                            "prefix": "1.2.3.5/32"
                                        },
                                        "prefix": "1.2.3.5/32",
                                        "next-hops": {
                                            "next-hop": [
                                                {
                                                    "config": {
                                                        "next-hop": "10.0.2.2",
                                                        "index": "**10.0.2.2**"
                                                    },
                                                    "index": "**10.0.2.2**"
                                                }
                                            ]
                                        }
                                    }
                                ]
                            },
                            "identifier": "openconfig-policy-types:STATIC"
                        },
                        {
                            "name": "default",
                            "config": {
                                "name": "default",
                                "identifier": "openconfig-policy-types:BGP"
                            },
                            "bgp": {
                                "global": {
                                    "afi-safis": {
                                        "afi-safi": [
                                            {
                                                "config": {
                                                    "afi-safi-name": "IPV4_UNICAST",
                                                    "enabled": true
                                                },
                                                "afi-safi-name": "IPV4_UNICAST"
                                            }
                                        ]
                                    },
                                    "config": {
                                        "router-id": "11.1.1.10",
                                        "as": 65400
                                    }
                                },
                                "neighbors": {
                                    "neighbor": [
                                        {
                                            "config": {
                                                "neighbor-address": "11.1.1.20",
                                                "peer-as": 65450
                                            },
                                            "afi-safis": {
                                                "afi-safi": [
                                                    {
                                                        "config": {
                                                            "afi-safi-name": "IPV4_UNICAST",
                                                            "enabled": true
                                                        },
                                                        "afi-safi-name": "IPV4_UNICAST"
                                                    }
                                                ]
                                            },
                                            "neighbor-address": "11.1.1.20"
                                        }
                                    ]
                                }
                            },
                            "identifier": "openconfig-policy-types:BGP"
                        }
                    ]
                },
                "config": {
                    "name": "default"
                }
            }
        ]
    },
    "Cisco-IOS-XR-man-netconf-cfg:netconf-yang": {
        "agent": {
            "ssh": {
                "enable": [
                    null
                ]
            }
        }
    },
    "openconfig-lacp:lacp": {
        "interfaces": {
            "interface": [
                {
                    "name": "MgmtEth0/RP0/CPU0/0",
                    "config": {
                        "name": "MgmtEth0/RP0/CPU0/0"
                    }
                },
                {
                    "name": "GigabitEthernet0/0/0/0",
                    "config": {
                        "name": "GigabitEthernet0/0/0/0"
                    }
                },
                {
                    "name": "GigabitEthernet0/0/0/1",
                    "config": {
                        "name": "GigabitEthernet0/0/0/1"
                    }
                },
                {
                    "name": "GigabitEthernet0/0/0/2",
                    "config": {
                        "name": "GigabitEthernet0/0/0/2"
                    }
                },
                {
                    "name": "GigabitEthernet0/0/0/3",
                    "config": {
                        "name": "GigabitEthernet0/0/0/3"
                    }
                },
                {
                    "name": "GigabitEthernet0/0/0/4",
                    "config": {
                        "name": "GigabitEthernet0/0/0/4"
                    }
                }
            ]
        }
    },
    "Cisco-IOS-XR-ifmgr-cfg:interface-configurations": {
        "interface-configuration": [
            {
                "description": "*** MANAGEMENT INTERFACE ***",
                "interface-name": "MgmtEth0/RP0/CPU0/0",
                "active": "act",
                "Cisco-IOS-XR-ipv4-io-cfg:ipv4-network": {
                    "addresses": {
                        "dhcp": {
                            "pattern": "MgmtEth0_RP0_CPU0_0",
                            "enabled": [
                                null
                            ]
                        }
                    }
                }
            },
            {
                "Cisco-IOS-XR-ipv6-ma-cfg:ipv6-network": {
                    "addresses": {
                        "auto-configuration": {
                            "enable": [
                                null
                            ]
                        },
                        "regular-addresses": {
                            "regular-address": [
                                {
                                    "address": "1010:1010::10",
                                    "zone": "0",
                                    "prefix-length": 64
                                }
                            ]
                        }
                    }
                },
                "interface-name": "GigabitEthernet0/0/0/0",
                "active": "act"
            },
            {
                "Cisco-IOS-XR-ipv6-ma-cfg:ipv6-network": {
                    "addresses": {
                        "auto-configuration": {
                            "enable": [
                                null
                            ]
                        },
                        "regular-addresses": {
                            "regular-address": [
                                {
                                    "address": "2020:2020::10",
                                    "zone": "0",
                                    "prefix-length": 64
                                }
                            ]
                        }
                    }
                },
                "interface-name": "GigabitEthernet0/0/0/1",
                "active": "act"
            },
            {
                "shutdown": [
                    null
                ],
                "interface-name": "GigabitEthernet0/0/0/2",
                "active": "act"
            },
            {
                "shutdown": [
                    null
                ],
                "interface-name": "GigabitEthernet0/0/0/3",
                "active": "act"
            },
            {
                "shutdown": [
                    null
                ],
                "interface-name": "GigabitEthernet0/0/0/4",
                "active": "act"
            }
        ]
    },
    "Cisco-IOS-XR-ipv4-bgp-cfg:bgp": {
        "instance": [
            {
                "instance-as": [
                    {
                        "as": 0,
                        "four-byte-as": [
                            {
                                "bgp-running": [
                                    null
                                ],
                                "as": 65400,
                                "default-vrf": {
                                    "global": {
                                        "router-id": "11.1.1.10",
                                        "global-afs": {
                                            "global-af": [
                                                {
                                                    "enable": [
                                                        null
                                                    ],
                                                    "af-name": "ipv4-unicast",
                                                    "sourced-networks": {
                                                        "sourced-network": [
                                                            {
                                                                "network-prefix": 24,
                                                                "network-addr": "11.1.1.0"
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    "bgp-entity": {
                                        "neighbors": {
                                            "neighbor": [
                                                {
                                                    "neighbor-address": "11.1.1.20",
                                                    "neighbor-afs": {
                                                        "neighbor-af": [
                                                            {
                                                                "activate": [
                                                                    null
                                                                ],
                                                                "af-name": "ipv4-unicast",
                                                                "next-hop-self": true
                                                            }
                                                        ]
                                                    },
                                                    "remote-as": {
                                                        "as-xx": 0,
                                                        "as-yy": 65450
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ],
                "instance-name": "default"
            }
        ]
    },
    "Cisco-IOS-XR-sysadmin-fpd-infra-cli-fpd:fpd": {
        "config": {
            "auto-upgrade": "disable"
        }
    },
    "openconfig-interfaces:interfaces": {
        "interface": [
            {
                "name": "MgmtEth0/RP0/CPU0/0",
                "config": {
                    "name": "MgmtEth0/RP0/CPU0/0",
                    "type": "iana-if-type:ethernetCsmacd",
                    "description": "*** MANAGEMENT INTERFACE ***",
                    "enabled": true
                },
                "openconfig-if-ethernet:ethernet": {
                    "config": {
                        "auto-negotiate": false
                    }
                }
            },
            {
                "name": "GigabitEthernet0/0/0/0",
                "subinterfaces": {
                    "subinterface": [
                        {
                            "openconfig-if-ip:ipv6": {
                                "addresses": {
                                    "address": [
                                        {
                                            "config": {
                                                "prefix-length": 64,
                                                "ip": "1010:1010::10"
                                            },
                                            "ip": "1010:1010::10"
                                        }
                                    ]
                                },
                                "config": {
                                    "enabled": true
                                }
                            },
                            "index": 0
                        }
                    ]
                },
                "config": {
                    "name": "GigabitEthernet0/0/0/0",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": true
                },
                "openconfig-if-ethernet:ethernet": {
                    "config": {
                        "auto-negotiate": false
                    }
                }
            },
            {
                "name": "GigabitEthernet0/0/0/1",
                "subinterfaces": {
                    "subinterface": [
                        {
                            "openconfig-if-ip:ipv6": {
                                "addresses": {
                                    "address": [
                                        {
                                            "config": {
                                                "prefix-length": 64,
                                                "ip": "2020:2020::10"
                                            },
                                            "ip": "2020:2020::10"
                                        }
                                    ]
                                },
                                "config": {
                                    "enabled": true
                                }
                            },
                            "index": 0
                        }
                    ]
                },
                "config": {
                    "name": "GigabitEthernet0/0/0/1",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": true
                },
                "openconfig-if-ethernet:ethernet": {
                    "config": {
                        "auto-negotiate": false
                    }
                }
            },
            {
                "name": "GigabitEthernet0/0/0/2",
                "config": {
                    "name": "GigabitEthernet0/0/0/2",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": false
                },
                "openconfig-if-ethernet:ethernet": {
                    "config": {
                        "auto-negotiate": false
                    }
                }
            },
            {
                "name": "GigabitEthernet0/0/0/3",
                "config": {
                    "name": "GigabitEthernet0/0/0/3",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": false
                },
                "openconfig-if-ethernet:ethernet": {
                    "config": {
                        "auto-negotiate": false
                    }
                }
            },
            {
                "name": "GigabitEthernet0/0/0/4",
                "config": {
                    "name": "GigabitEthernet0/0/0/4",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": false
                },
                "openconfig-if-ethernet:ethernet": {
                    "config": {
                        "auto-negotiate": false
                    }
                }
            }
        ]
    },
    "Cisco-IOS-XR-tty-vty-cfg:vty": {
        "vty-pools": {
            "vty-pool": [
                {
                    "line-template": "VTY-TEMPLATE",
                    "first-vty": 0,
                    "last-vty": 4,
                    "pool-name": "default"
                }
            ]
        }
    },
    "Cisco-IOS-XR-shellutil-cfg:host-names": {
        "host-name": "r1"
    },
    "Cisco-IOS-XR-aaa-lib-cfg:aaa": {
        "Cisco-IOS-XR-aaa-locald-cfg:usernames": {
            "username": [
                {
                    "name": "admin",
                    "secret": "$1$A4C9$oaNorr6BXDruE4gDd086L.",
                    "usergroup-under-usernames": {
                        "usergroup-under-username": [
                            {
                                "name": "root-lr"
                            },
                            {
                                "name": "cisco-support"
                            }
                        ]
                    },
                    "ordering-index": 0
                }
            ]
        }
    },
    "Cisco-IOS-XR-crypto-ssh-cfg:ssh": {
        "server": {
            "netconf-vrf-table": {
                "vrf": [
                    {
                        "enable": [
                            null
                        ],
                        "vrf-name": "default"
                    }
                ]
            },
            "v2": [
                null
            ]
        }
    },
    "openconfig-telemetry:telemetry-system": {
        "subscriptions": {
            "persistent": {
                "subscription": [
                    {
                        "subscription-id": "IPV6",
                        "sensor-profiles": {
                            "sensor-profile": [
                                {
                                    "sensor-group": "IPV6Neighbor",
                                    "config": {
                                        "sensor-group": "IPV6Neighbor",
                                        "sample-interval": "15000"
                                    }
                                }
                            ]
                        },
                        "config": {
                            "subscription-id": "IPV6"
                        }
                    },
                    {
                        "subscription-id": "Sub1",
                        "sensor-profiles": {
                            "sensor-profile": [
                                {
                                    "sensor-group": "SGroup1",
                                    "config": {
                                        "sensor-group": "SGroup1",
                                        "sample-interval": "30000"
                                    }
                                }
                            ]
                        },
                        "config": {
                            "subscription-id": "Sub1"
                        },
                        "destination-groups": {
                            "destination-group": [
                                {
                                    "config": {
                                        "group-id": "DGroup1"
                                    },
                                    "group-id": "DGroup1"
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "sensor-groups": {
            "sensor-group": [
                {
                    "sensor-paths": {
                        "sensor-path": [
                            {
                                "path": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters",
                                "config": {
                                    "path": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters"
                                }
                            }
                        ]
                    },
                    "config": {
                        "sensor-group-id": "SGroup1"
                    },
                    "sensor-group-id": "SGroup1"
                },
                {
                    "sensor-paths": {
                        "sensor-path": [
                            {
                                "path": "Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address",
                                "config": {
                                    "path": "Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address"
                                }
                            }
                        ]
                    },
                    "config": {
                        "sensor-group-id": "IPV6Neighbor"
                    },
                    "sensor-group-id": "IPV6Neighbor"
                }
            ]
        },
        "destination-groups": {
            "destination-group": [
                {
                    "destinations": {
                        "destination": [
                            {
                                "destination-port": 5432,
                                "config": {
                                    "destination-port": 5432,
                                    "destination-protocol": "TCP",
                                    "destination-address": "192.168.122.11"
                                },
                                "destination-address": "192.168.122.11"
                            }
                        ]
                    },
                    "config": {
                        "group-id": "DGroup1"
                    },
                    "group-id": "DGroup1"
                }
            ]
        }
    },
    "Cisco-IOS-XR-infra-syslog-cfg:syslog": {
        "console-logging": {
            "logging-level": "debug"
        }
    },
    "Cisco-IOS-XR-man-ems-cfg:grpc": {
        "port": 57777,
        "service-layer": {
            "enable": [
                null
            ]
        },
        "enable": [
            null
        ],
        "no-tls": [
            null
        ]
    },
    "Cisco-IOS-XR-ip-static-cfg:router-static": {
        "default-vrf": {
            "address-family": {
                "vrfipv4": {
                    "vrf-unicast": {
                        "vrf-prefixes": {
                            "vrf-prefix": [
                                {
                                    "vrf-route": {
                                        "vrf-next-hop-table": {
                                            "vrf-next-hop-next-hop-address": [
                                                {
                                                    "next-hop-address": "10.0.2.2"
                                                }
                                            ]
                                        }
                                    },
                                    "prefix-length": 0,
                                    "prefix": "0.0.0.0"
                                },
                                {
                                    "vrf-route": {
                                        "vrf-next-hop-table": {
                                            "vrf-next-hop-next-hop-address": [
                                                {
                                                    "next-hop-address": "10.0.2.2"
                                                }
                                            ]
                                        }
                                    },
                                    "prefix-length": 32,
                                    "prefix": "1.2.3.5"
                                }
                            ]
                        }
                    }
                }
            }
        }
    },
    "Cisco-IOS-XR-telemetry-model-driven-cfg:telemetry-model-driven": {
        "enable": [
            null
        ],
        "subscriptions": {
            "subscription": [
                {
                    "sensor-profiles": {
                        "sensor-profile": [
                            {
                                "sample-interval": 15000,
                                "sensorgroupid": "IPV6Neighbor"
                            }
                        ]
                    },
                    "subscription-identifier": "IPV6"
                },
                {
                    "destination-profiles": {
                        "destination-profile": [
                            {
                                "destination-id": "DGroup1"
                            }
                        ]
                    },
                    "sensor-profiles": {
                        "sensor-profile": [
                            {
                                "sample-interval": 30000,
                                "sensorgroupid": "SGroup1"
                            }
                        ]
                    },
                    "subscription-identifier": "Sub1"
                }
            ]
        },
        "sensor-groups": {
            "sensor-group": [
                {
                    "sensor-paths": {
                        "sensor-path": [
                            {
                                "telemetry-sensor-path": "Cisco-IOS-XR-infra-statsd-oper:infra-statistics/interfaces/interface/latest/generic-counters"
                            }
                        ]
                    },
                    "sensor-group-identifier": "SGroup1"
                },
                {
                    "sensor-paths": {
                        "sensor-path": [
                            {
                                "telemetry-sensor-path": "Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address"
                            }
                        ]
                    },
                    "sensor-group-identifier": "IPV6Neighbor"
                }
            ]
        },
        "destination-groups": {
            "destination-group": [
                {
                    "ipv4-destinations": {
                        "ipv4-destination": [
                            {
                                "destination-port": 5432,
                                "protocol": {
                                    "no-tls": 1,
                                    "protocol": "tcp"
                                },
                                "ipv4-address": "192.168.122.11",
                                "encoding": "self-describing-gpb"
                            }
                        ]
                    },
                    "destination-id": "DGroup1"
                }
            ]
        }
    },
    "Cisco-IOS-XR-sysadmin-services:service": {
        "cli": {
            "interactive": {
                "enabled": true
            }
        }
    },
    "Cisco-IOS-XR-call-home-cfg:call-home": {
        "contact-smart-licensing": true,
        "profiles": {
            "profile": [
                {
                    "profile-name": "CiscoTAC-1",
                    "active": [
                        null
                    ],
                    "create": [
                        null
                    ],
                    "methods": {
                        "method": [
                            {
                                "enable": false,
                                "method": "email"
                            },
                            {
                                "enable": true,
                                "method": "http"
                            }
                        ]
                    }
                }
            ]
        },
        "active": [
            null
        ]
    },
    "Cisco-IOS-XR-infra-syslog-cfg:syslog-service": {
        "timestamps": {
            "log": {
                "log-datetime": {
                    "log-datetime-value": {
                        "msec": "enable"
                    }
                }
            },
            "debug": {
                "debug-datetime": {
                    "datetime-value": {
                        "msec": "enable"
                    }
                }
            }
        }
    },
    "Cisco-IOS-XR-infra-infra-cfg:banners": {
        "banner": [
            {
                "banner-text": ";\n--------------------------------------------------------------------------\n  Router 1 (Cisco IOS XR Sandbox)\n--------------------------------------------------------------------------\n;",
                "banner-name": "motd"
            }
        ]
    }
}


```


Massage the files to extract the content you need and start migrating your CLI configs to YANG today!



