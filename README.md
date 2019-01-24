# cli2yang-tools
Simple tools to convert existing CLI configurations to YANG formats (XML, JSON)

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

## Converting CLI configuration to YANG XML

The goal is to convert a given CLI configuration into corresponding XML [(RFC7950)](https://tools.ietf.org/html/rfc7950) and JSON [(RFC7951)](https://tools.ietf.org/html/rfc7951) based on the Yang models supported by the router.

**Note**: In the current version, only XML (RFC7950) is supported. We will add support for JSON(RFC 7951) soon through IOS-XR's GNMI support.



## Before we Begin

A few groundkeeping tasks on the router running IOS-XR (tested: 6.2.25+) before we run the code.

### Enable netconf and SSH on the router

We expect a minimum base configuration on the router to begin with. A separate base.config is also applied by the script during its running process to normalize the bvbase state before creating a diff.

The minimum base config is given below (note that the username/password could be set to whatever you need, and MgmtIP can be static and reachable. Rest is mandatory)

```
!! IOS XR Configuration
!! Last configuration change at Thu Jan 24 05:21:03 2019 by vagrant
!
hostname ios
username vagrant
 group root-lr
 group cisco-support
 secret 5 $1$FTjI$nxqpDLAdVH1E3agGiVOdT0
!
interface MgmtEth0/RP0/CPU0/0
 ipv4 address dhcp
!
!
netconf-yang agent
 ssh
!
ssh server v2
ssh server vrf default
end
```


### Set up OpenSSH session in IOS-XR bash

Drop into IOS-XR bash shell and start the sshd_operns service


```
RP/0/RP0/CPU0:ios#
RP/0/RP0/CPU0:ios#bash
Thu Jan 24 08:22:40.589 UTC
RP/0/RP0/CPU0:Jan 24 08:22:40.673 UTC: bash_cmd[67017]: %INFRA-INFRA_MSG-5-RUN_LOGIN : User root logged into shell from con0/RP0/CPU0 


[ios:~]$ 
[ios:~]$ 
[ios:~]$ service sshd_operns start
SSH service for global-vrf has been created. You may use 'service sshd_operns_global-vrf <start|stop|reload|restart|status>'. 
Service can be configured to run on reload using 'chkconfig --add sshd_operns_global-vrf' 
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: Waiting for OPERNS interface creation...
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: Press ^C to stop if needed.
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: Found nic, Tg0_0_0_0
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: Waiting for OPERNS management interface creation...
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: Found nic, Mg0_RP0_CPU0_0
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: OPERNS is ready
Thu Jan 24 08:23:30 UTC 2019 /etc/init.d/sshd_operns: Start sshd_operns
Starting OpenBSD Secure Shell server: sshd
[ios:~]$ 

```

This will start sshd on port 57722 in the Linux kernel:

```
RP/0/RP0/CPU0:rtr2#bash
Thu Jan 24 08:24:59.177 UTC
RP/0/RP0/CPU0:Jan 24 08:24:59.261 UTC: bash_cmd[67681]: %INFRA-INFRA_MSG-5-RUN_LOGIN : User root logged into shell from con0/RP0/CPU0 

[rtr2:~]$ 
[rtr2:~]$ netstat -nlp | grep 57722
tcp        0      0 0.0.0.0:57722           0.0.0.0:*               LISTEN      18382/sshd      
tcp6       0      0 :::57722                :::*                    LISTEN      18382/sshd      
[rtr2:~]$ 


```


### Set up a user in the shell and add to /etc/sudoers

We'll be using ZTP CLI hooks to do CLI operations in tandem with netconf (and gRPC in the future) to validate that the device gets into the correct CLI state using the XML and JSON YANG representations that we derive.

To perform these ZTP operations seamlessly over SSH, we set up a sudo user and give it privileges to do without needing a password.
It goes without saying: DO NOT DO THIS IN PRODUCTION. This is just to create a setup to ease the process of converting CLIs configs to YANG RPCs. Try it out on a private setup or virtual router meant for development and create the repository of YANG RPCs you can then deploy on production routers.


Again drop to bash and use `adduser`:
You can choose whatever username/password combination you want.

```
RP/0/RP0/CPU0:rtr2#bash
Thu Jan 24 08:24:59.177 UTC
RP/0/RP0/CPU0:
[rtr2:~]$ adduser vagrant
Login name for new user []:vagrant

User id for vagrant [ defaults to next available]:

Initial group for vagrant [users]:

Additional groups for vagrant []:sudo

vagrant's home directory [/home/vagrant]:

vagrant's shell [/bin/bash]:

vagrant's account expiry date (MM/DD/YY) []:

OK, Im about to make a new account. Heres what you entered so far:
New login name: vagrant
New UID: [Next available]
Initial group: users
/usr/sbin/adduser: line 68: [: -G: binary operator expected
Additional groups: sudo
Home directory: /home/vagrant
Shell: /bin/bash
Expiry date: [no expiration]
This is it... if you want to bail out, you'd better do it now.

Making new account...
useradd: user 'vagrant' already exists
Changing the user information for vagrant
Enter the new value, or press ENTER for the default
	Full Name []: 
	Room Number []: 
	Work Phone []: 
	Home Phone []: 
	Other []: 
Enter new UNIX password: 
Retype new UNIX password: 
passwd: password updated successfully
Done...
[rtr2:~]$ 
[rtr2:~]$ 
[rtr2:~]$ 
[rtr2:~]$ id vagrant
uid=1000(vagrant) gid=1009(vagrant) groups=1009(vagrant),27(sudo),1000(cisco-support),1005(root-lr)
[rtr2:~]$ 

```

Add the created user with NOPASSWD facility to become sudo without prompts:

```
[rtr2:~]$ 
[rtr2:~]$ echo "vagrant ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers


```


### Add your SSH keys to the router's shell

Finally, to enable password-free operation for the ZTP CLI hooks over SSH, add your client machine's (where this code will be running) public key to the user's (the one you created above) `authorized_keys` file.

To do this on an XR box (which has restrictive permissions for non root users), ssh locally in the bash shell using the username/password you just created above.
You will then logged in as the user created (in our case: `vagrant`):

```
RP/0/RP0/CPU0:rtr2#bash
Thu Jan 24 08:24:59.177 UTC
[rtr2:~]$ 
[rtr2:~]$ ssh -p 57722 vagrant@localhost
vagrant@localhost's password: 
Last login: Thu Jan 24 08:46:12 2019 from 11.11.11.2
-sh: /var/log/boot.log: Permission denied
-sh: /var/log/boot.log: Permission denied
-sh: /var/log/boot.log: Permission denied
rtr2:~$ 
rtr2:~$ 
rtr2:~$ 
rtr2:~$ ssh-keygen -t rsa
Generating public/private rsa key pair.
Enter file in which to save the key (/home/vagrant/.ssh/id_rsa): 
Created directory '/home/vagrant/.ssh'.
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/vagrant/.ssh/id_rsa.
Your public key has been saved in /home/vagrant/.ssh/id_rsa.pub.
The key fingerprint is:
f9:7e:ab:0e:4a:7c:89:bd:7a:a4:fe:b9:58:4e:1a:af vagrant@rtr2
The key's randomart image is:
+--[ RSA 2048]----+
|                 |
|                 |
|                 |
|         .       |
|        S        |
|     . o.o       |
|      =oB .      |
|     ..@.=  .    |
|     .E=Bo+o..   |
+-----------------+
rtr2:~$ 
rtr2:~$ 
rtr2:~$ cat .ssh/authorized_keys 
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsXA/klX56NGMGUW+04pG3Adh9kB9QjVeyMKqRQmubvN+3V/tB3Wyha7sqKGJrf7yJ+l+AO1N+pvPyzPuVTZI3JSwDHCMHNxSN8/Pgw486ghwFEB8RO/xfhHt+BDTYD4vA6jEu5Y8Eg92mX/aVv4jm1NQU87a7yuwT5Eto6pPwhztB2rnstDuJDgj5jm3+jWOGB57CP6PARuqtdosT1OEiLQY/OH1vWe5mADh1B5EqyCa/AuSyBCJle9J7q6uxqVrsC6a1/JTbOVftleibENnHy6xNzMSvM3E31shAENm01hyGbQ803c1lSbZ0K0jDsSFHdHRdgpjil9ddWpZi0x75 cisco@dhcpserver
rtr2:~$ 

```
 

You should now be able to login to the shell of the XR router using the created user and become sudo without a password!:

```
cisco@dhcpserver:~$ 
cisco@dhcpserver:~$ ssh -p 57722 vagrant@11.11.11.33
Last login: Thu Jan 24 08:58:52 2019 from 11.11.11.2
-sh: /var/log/boot.log: Permission denied
-sh: /var/log/boot.log: Permission denied
-sh: /var/log/boot.log: Permission denied
rtr2:~$ 
rtr2:~$ whoami
vagrant
rtr2:~$ 
rtr2:~$ sudo -i
[rtr2:~]$ 
[rtr2:~]$ whoami
root
[rtr2:~]$ 

```


## Run the script

Run the script against the router. Before starting, dump the options available:

```
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -h
usage: cli2xmljson.py [-h] [-s HOST] [-n NC_PORT] [-g GRPC_PORT]
                      [-l XR_LNX_SSH_PORT] [-u USERNAME] [-p PASSWORD]
                      [-c INPUT_CLI_FILE] [-b BASE_CONFIG_FILE] [-d] [-t]
                      [-x NC_XML_FILE] [-j GRPC_JSON_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --server HOST
                        IP address of netconf server and gRPC server on the
                        router
  -n NC_PORT, --netconf-port NC_PORT
                        netconf port
  -g GRPC_PORT, --grpc-port GRPC_PORT
                        gRPC port -- IMPORTANT: Not supported in this version.
                        Support using GNMI will be brought in soon.
  -l XR_LNX_SSH_PORT, --xr-lnx-ssh-port XR_LNX_SSH_PORT
                        XR linux shell SSH port
  -u USERNAME, --username USERNAME
                        IOS-XR AAA username
  -p PASSWORD, --password PASSWORD
                        IOS-XR AAA password
  -c INPUT_CLI_FILE, --input-cli-file INPUT_CLI_FILE
                        Specify input file path for CLI configuration to
                        convert into netconf RPC
  -b BASE_CONFIG_FILE, --base-config-file BASE_CONFIG_FILE
                        Specify file path for base CLI configuration to apply
                        to device before starting, by default: ./base.config
  -d, --debug           Enable debugging
  -t, --test-merge      Test config merge with each output file
  -x NC_XML_FILE, --nc-xml-file NC_XML_FILE
                        Specify output file path for netconf based XML output
  -j GRPC_JSON_FILE, --grpc-json-file GRPC_JSON_FILE
                        Specify output file path for gRPC based JSON output
cisco@ubuntu:~/cli2yang-tools$ 
```


For the router configured with netconf and gRPC as shown above, run the script like so:

**Note**:  Some sample config files are provided as part of the code. Use them to test the script against your IOS-XR router with the `-c` option as shown below.


```

co@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -s jumphost -n 2202 -l 57723 -c ./bgp.config -u vagrant -p vagrant -t
Replacing existing router configuration with the specified base_config using file:./base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
Testing the generated YANG XML by doing a merge config....
Successful!!
The CLI configuration created by applying the generated YANG XML is...


!! IOS XR Configuration 
router bgp 65001
 address-family ipv4 unicast
 !
 neighbor-group IBGP
  remote-as 65001
  update-source Loopback0
  address-family ipv4 unicast
  !
 !
 neighbor 172.16.255.2
  use neighbor-group IBGP
 !
!
end


Input CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Finally resetting the router back to its original configuration
cisco@ubuntu:~/cli2yang-tools$ 

```

### Verify the files created

For the input configuration file like so:



```
cisco@ubuntu:~/cli2yang-tools$ cat ./bgp.config 
router bgp 65001
 address-family ipv4 unicast
 !
 neighbor-group IBGP
  remote-as 65001
  update-source Loopback0
  address-family ipv4 unicast
  !
 !
 neighbor 172.16.255.2
  use neighbor-group IBGP
 !
!
end
cisco@ubuntu:~/cli2yang-tools$ 

```

The YANG XML file created by the script ends up looking something like:  

(Use this file to directly do a config-merge/config-replace over netconf).


```xml
cisco@ubuntu:~/cli2yang-tools$ cat ./yang_nc.xml 
<?xml version="1.0" encoding="utf-8"?>
<config>
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
								<as>65001</as>
							</config>
							<afi-safis>
								<afi-safi>
									<afi-safi-name xmlns:idx="http://openconfig.net/yang/bgp-types">idx:IPV4_UNICAST</afi-safi-name>
									<config>
										<afi-safi-name xmlns:idx="http://openconfig.net/yang/bgp-types">idx:IPV4_UNICAST</afi-safi-name>
										<enabled>true</enabled>
									</config>
								</afi-safi>
							</afi-safis>
						</global>
						<peer-groups>
							<peer-group>
								<peer-group-name>IBGP</peer-group-name>
								<config>
									<peer-group-name>IBGP</peer-group-name>
									<peer-as>65001</peer-as>
								</config>
								<afi-safis>
									<afi-safi>
										<afi-safi-name xmlns:idx="http://openconfig.net/yang/bgp-types">idx:IPV4_UNICAST</afi-safi-name>
										<config>
											<afi-safi-name xmlns:idx="http://openconfig.net/yang/bgp-types">idx:IPV4_UNICAST</afi-safi-name>
											<enabled>true</enabled>
										</config>
									</afi-safi>
								</afi-safis>
							</peer-group>
						</peer-groups>
						<neighbors>
							<neighbor>
								<neighbor-address>172.16.255.2</neighbor-address>
								<config>
									<neighbor-address>172.16.255.2</neighbor-address>
									<peer-group>IBGP</peer-group>
								</config>
							</neighbor>
						</neighbors>
					</bgp>
				</protocol>
			</protocols>
		</network-instance>
	</network-instances>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65001</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<global-afs>
								<global-af>
									<af-name>ipv4-unicast</af-name>
									<enable></enable>
								</global-af>
							</global-afs>
						</global>
						<bgp-entity>
							<neighbor-groups>
								<neighbor-group>
									<neighbor-group-name>IBGP</neighbor-group-name>
									<create></create>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65001</as-yy>
									</remote-as>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-group-afs>
										<neighbor-group-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
										</neighbor-group-af>
									</neighbor-group-afs>
								</neighbor-group>
							</neighbor-groups>
							<neighbors>
								<neighbor>
									<neighbor-address>172.16.255.2</neighbor-address>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
								</neighbor>
							</neighbors>
						</bgp-entity>
					</default-vrf>
				</four-byte-as>
			</instance-as>
		</instance>
	</bgp>
</config>

```
