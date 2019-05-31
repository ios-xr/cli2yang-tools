# cli2yang-tools
Simple tools to convert existing CLI configurations to YANG formats (XML, JSON)

## cli2xmljson.py
The purpose of the script cli2xmljson.py is to be able to convert any input CLI snippet into a corresponding yang RPC and test the yang equivalent on an IOS-XR router (tested on release >6.5.2)
to an equivalent YANG-Based XML rendering for use over netconf and YANG-Based JSON rendering for use over gRPC (Not ready yet).

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

We expect a minimum base configuration on the router to begin with. A separate base.config is also applied by the script during its running process to normalize the base state before creating a diff.

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
                      [-x NC_XML_FILE] [-v] [-j GRPC_JSON_FILE] [-o]

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
  -v, --verbose         Enable verbose logging - useful for debugging ncclient
                        RPCs
  -j GRPC_JSON_FILE, --grpc-json-file GRPC_JSON_FILE
                        Specify output file path for gRPC based JSON output
  -o, --openconfig      Enable translation of CLI into openconfig model - by
                        default it is off. This is done because not all XR
                        platforms respond with Openconfig equivalent in GET
                        requests but do respond with Native model formats.
                        Also some Openconfig models have been in flux and
                        testing the models sometimes fails. If it works, try
                        the -o flag along with the -t flag. If test fails, use
                        the -o flag without the -t flag to atleast get the
                        openconfig equivalent where possible. Else skip the -o
                        flag altogether.
cisco@ubuntu:~/cli2yang-tools$ 
```


For the router configured with netconf as shown above, run the script like so:

**Note**:  Some sample config files are provided as part of the code. Use them to test the script against your IOS-XR router with the `-c` option as shown below.


## Examples

### Converting Basic lldp config into yang xml

The lldp config snippet is in the file `lldp.config`:

```
cisco@ubuntu:~/cli2yang-tools$ cat lldp.config 
!
lldp
!
end
cisco@ubuntu:~/cli2yang-tools$ 

```

#### Native XR model output

Running the code without the `-o' flag. This will create the yang equivalent with the native XR model alone.

```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c lldp.config -n 2201 -l 2221 -u vagrant -p vagrant -s localhost -t  
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
ssh: connect to host localhost port 2221: Connection refused
lost connection
Failed to transfer configuration file to router
Failed to replace base configuration of router before starting with file:
ncs5500_base.config
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c lldp.config -n 2201 -l 2221 -u vagrant -p vagrant -s 10.30.110.215 -t  
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
##################################################
YANG XML version of the input CLI configuration:
##################################################
<?xml version="1.0" encoding="utf-8"?>
<config>
	<lldp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ethernet-lldp-cfg">
		<enable>true</enable>
	</lldp>
</config>
Testing the generated YANG XML by doing a merge config....
Successful!!
The CLI configuration created by applying the generated YANG XML is...


!! IOS XR Configuration version = 6.5.2.28I
lldp
!
end


Input CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Finally resetting the router back to its original configuration
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 

```

Dump the file `yang_nc.xml` to view the translated content - you can also view it in the output above:

```
cisco@ubuntu:~/cli2yang-tools$ cat yang_nc.xml 
<?xml version="1.0" encoding="utf-8"?>
<config>
	<lldp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ethernet-lldp-cfg">
		<enable>true</enable>
	</lldp>
</config>
``` 

#### Native XR model + Openconfig Model

Now enable the openconfig model processing using the `-o` flag. An appropriate warning will be displayed for now.

```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c lldp.config -n 2201 -l 2221 -u vagrant -p vagrant -s 10.30.110.215 -t  -o
WARNING: not all XR platforms respond with Openconfig equivalent in GET requests but do respond with Native model formats. Also some Openconfig models have been in flux and testing the models sometimes fails. 
 If it works, try the -o flag along with the -t flag. If test fails, use the -o flag without the -t flag to atleast get the openconfig equivalent where possible. Else skip the -o flag altogether.
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
##################################################
YANG XML version of the input CLI configuration:
##################################################
<?xml version="1.0" encoding="utf-8"?>
<config>
	<lldp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ethernet-lldp-cfg">
		<enable>true</enable>
	</lldp>
	<lldp xmlns="http://openconfig.net/yang/lldp">
		<config>
			<enabled>true</enabled>
		</config>
	</lldp>
</config>
Testing the generated YANG XML by doing a merge config....
Successful!!
The CLI configuration created by applying the generated YANG XML is...


!! IOS XR Configuration version = 6.5.2.28I
lldp
!
end


Input CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Finally resetting the router back to its original configuration
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
```

Dumping the output:

```
<?xml version="1.0" encoding="utf-8"?>
<config>
	<lldp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ethernet-lldp-cfg">
		<enable>true</enable>
	</lldp>
	<lldp xmlns="http://openconfig.net/yang/lldp">
		<config>
			<enabled>true</enabled>
		</config>
	</lldp>
</config>

```


### Converting a full final NCS5500 cli configuration into YANG xml

Dumping the sample final configuration:


```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ cat ncs5500_final.config 
!! IOS XR Configuration version = 6.5.2.28I
!! Last configuration change at Tue Feb 12 09:33:35 2019 by vagrant
!
logging console debugging
domain name cisco.com
username vagrant
 group root-lr
 group cisco-support
 secret 5 $1$FzMk$Y5G3Cv0H./q0fG.LGyIJS1
!
username root
 group root-lr
 group cisco-support
 secret 5 $1$7kTu$zjrgqbgW08vEXsYzUycXw1
!
address-family ipv4 unicast
!
interface Loopback0
 ipv4 address 50.1.1.1 255.255.255.255
!
interface MgmtEth0/RP0/CPU0/0
 ipv4 address 11.11.11.23 255.255.255.0
!         
interface TenGigE0/0/0/1
 shutdown
!
interface TenGigE0/0/0/2
 shutdown
!
interface TenGigE0/0/0/3
 shutdown
!
interface TenGigE0/0/0/4
 shutdown
!
interface TenGigE0/0/0/5
 shutdown
!
interface TenGigE0/0/0/6
 shutdown
!
interface TenGigE0/0/0/7
 shutdown
!
interface TenGigE0/0/0/8
 shutdown 
!
interface TenGigE0/0/0/9
 shutdown
!
interface TenGigE0/0/0/10
 shutdown
!
interface TenGigE0/0/0/11
 shutdown
!
interface TenGigE0/0/0/12
 shutdown
!
interface TenGigE0/0/0/13
 shutdown
!
interface TenGigE0/0/0/14
 shutdown
!
interface TenGigE0/0/0/15
 shutdown
!
interface TenGigE0/0/0/16
 shutdown
!
interface TenGigE0/0/0/17
 shutdown
!
interface TenGigE0/0/0/18
 shutdown
!
interface TenGigE0/0/0/19
 shutdown
!
interface TenGigE0/0/0/20
 shutdown
!
interface TenGigE0/0/0/21
 shutdown
!
interface TenGigE0/0/0/22
 shutdown
!
interface TenGigE0/0/0/23
 shutdown
!         
interface TenGigE0/0/0/24
 shutdown
!
interface TenGigE0/0/0/25
 shutdown
!
interface TenGigE0/0/0/26
 shutdown
!
interface TenGigE0/0/0/27
 shutdown
!
interface TenGigE0/0/0/28
 shutdown
!
interface TenGigE0/0/0/29
 shutdown
!
interface TenGigE0/0/0/30
 shutdown
!
interface TenGigE0/0/0/31
 shutdown 
!
interface TenGigE0/0/0/32
 shutdown
!
interface TenGigE0/0/0/33
 shutdown
!
interface TenGigE0/0/0/34
 shutdown
!
interface TenGigE0/0/0/35
 shutdown
!
interface TenGigE0/0/0/36
 shutdown
!
interface TenGigE0/0/0/37
 shutdown
!
interface TenGigE0/0/0/38
 shutdown
!
interface TenGigE0/0/0/39
 shutdown
!
interface TenGigE0/0/0/40
 shutdown
!
interface TenGigE0/0/0/41
 shutdown
!
interface TenGigE0/0/0/42
 shutdown
!
interface TenGigE0/0/0/43
 shutdown
!
interface TenGigE0/0/0/44
 shutdown
!
interface TenGigE0/0/0/45
 shutdown
!
interface TenGigE0/0/0/46
 shutdown
!         
interface TenGigE0/0/0/47
 shutdown
!
interface HundredGigE0/0/1/0
 ipv4 address 10.1.1.10 255.255.255.0
 ipv6 nd unicast-ra
 ipv6 enable
!
interface HundredGigE0/0/1/1
 ipv4 address 11.1.1.10 255.255.255.0
 ipv6 nd unicast-ra
 ipv6 enable
!
router ospf 100
 router-id 50.1.1.1
 area 0
  interface Loopback0
   passive enable
  !
  interface HundredGigE0/0/1/0
   network point-to-point
  !
  interface HundredGigE0/0/1/1
   network point-to-point
  !
 !
!
!
telemetry model-driven
 sensor-group BGP
  sensor-path Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active
 !
 sensor-group BGPSession
  sensor-path Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/sessions
  sensor-path Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/process-info
 !
 sensor-group IPV6Neighbor
  sensor-path Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address
 !
 subscription IPV6
  sensor-group-id IPV6Neighbor sample-interval 15000
 !
 subscription BGP-FULL
  sensor-group-id BGP sample-interval 15000
 !
 subscription BGP-SESSION
  sensor-group-id BGPSession sample-interval 15000
 !
!
netconf-yang agent
 ssh
!
ssh server v2
ssh server netconf vrf default
end
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 


```


Running the script with the `-o` flag to get both Native XR model and Openconfig Model outputs:


```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c ncs5500_final.config -n 2201 -l 2221 -u vagrant -p vagrant -s 10.30.110.215 -t  -o
WARNING: not all XR platforms respond with Openconfig equivalent in GET requests but do respond with Native model formats. Also some Openconfig models have been in flux and testing the models sometimes fails. 
 If it works, try the -o flag along with the -t flag. If test fails, use the -o flag without the -t flag to atleast get the openconfig equivalent where possible. Else skip the -o flag altogether.
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
##################################################
YANG XML version of the input CLI configuration:
##################################################
<?xml version="1.0" encoding="utf-8"?>
<config>
	<syslog xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-syslog-cfg">
		<console-logging>
			<logging-level>debug</logging-level>
		</console-logging>
	</syslog>
	<global-af xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-rsi-cfg">
		<afs>
			<af>
				<af-name>ipv4</af-name>
				<saf-name>unicast</saf-name>
				<topology-name>default</topology-name>
				<create></create>
			</af>
		</afs>
	</global-af>
	<ip-domain xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ip-domain-cfg">
		<vrfs>
			<vrf>
				<vrf-name>default</vrf-name>
				<name>cisco.com</name>
			</vrf>
		</vrfs>
	</ip-domain>
	<telemetry-model-driven xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-telemetry-model-driven-cfg">
		<sensor-groups>
			<sensor-group>
				<sensor-group-identifier>BGP</sensor-group-identifier>
				<sensor-paths>
					<sensor-path>
						<telemetry-sensor-path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active</telemetry-sensor-path>
					</sensor-path>
				</sensor-paths>
			</sensor-group>
			<sensor-group>
				<sensor-group-identifier>BGPSession</sensor-group-identifier>
				<sensor-paths>
					<sensor-path>
						<telemetry-sensor-path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/sessions</telemetry-sensor-path>
					</sensor-path>
					<sensor-path>
						<telemetry-sensor-path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/process-info</telemetry-sensor-path>
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
				<subscription-identifier>BGP-FULL</subscription-identifier>
				<sensor-profiles>
					<sensor-profile>
						<sensorgroupid>BGP</sensorgroupid>
						<sample-interval>15000</sample-interval>
					</sensor-profile>
				</sensor-profiles>
			</subscription>
			<subscription>
				<subscription-identifier>BGP-SESSION</subscription-identifier>
				<sensor-profiles>
					<sensor-profile>
						<sensorgroupid>BGPSession</sensorgroupid>
						<sample-interval>15000</sample-interval>
					</sensor-profile>
				</sensor-profiles>
			</subscription>
		</subscriptions>
	</telemetry-model-driven>
	<ospf xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-ospf-cfg">
		<processes>
			<process>
				<process-name>100</process-name>
				<default-vrf>
					<router-id>50.1.1.1</router-id>
					<area-addresses>
						<area-area-id>
							<area-id>0</area-id>
							<running></running>
							<name-scopes>
								<name-scope>
									<interface-name>Loopback0</interface-name>
									<running></running>
									<passive>true</passive>
								</name-scope>
								<name-scope>
									<interface-name>HundredGigE0/0/1/0</interface-name>
									<running></running>
									<network-type>point-to-point</network-type>
								</name-scope>
								<name-scope>
									<interface-name>HundredGigE0/0/1/1</interface-name>
									<running></running>
									<network-type>point-to-point</network-type>
								</name-scope>
							</name-scopes>
						</area-area-id>
					</area-addresses>
				</default-vrf>
				<start></start>
			</process>
		</processes>
	</ospf>
	<telemetry-system xmlns="http://openconfig.net/yang/telemetry">
		<sensor-groups>
			<sensor-group>
				<sensor-group-id>BGP</sensor-group-id>
				<config>
					<sensor-group-id>BGP</sensor-group-id>
				</config>
				<sensor-paths>
					<sensor-path>
						<path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active</path>
						<config>
							<path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active</path>
						</config>
					</sensor-path>
				</sensor-paths>
			</sensor-group>
			<sensor-group>
				<sensor-group-id>BGPSession</sensor-group-id>
				<config>
					<sensor-group-id>BGPSession</sensor-group-id>
				</config>
				<sensor-paths>
					<sensor-path>
						<path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/sessions</path>
						<config>
							<path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/sessions</path>
						</config>
					</sensor-path>
					<sensor-path>
						<path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/process-info</path>
						<config>
							<path>Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/process-info</path>
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
					<subscription-id>BGP-FULL</subscription-id>
					<config>
						<subscription-id>BGP-FULL</subscription-id>
					</config>
					<sensor-profiles>
						<sensor-profile>
							<sensor-group>BGP</sensor-group>
							<config>
								<sensor-group>BGP</sensor-group>
								<sample-interval>15000</sample-interval>
							</config>
						</sensor-profile>
					</sensor-profiles>
				</subscription>
				<subscription>
					<subscription-id>BGP-SESSION</subscription-id>
					<config>
						<subscription-id>BGP-SESSION</subscription-id>
					</config>
					<sensor-profiles>
						<sensor-profile>
							<sensor-group>BGPSession</sensor-group>
							<config>
								<sensor-group>BGPSession</sensor-group>
								<sample-interval>15000</sample-interval>
							</config>
						</sensor-profile>
					</sensor-profiles>
				</subscription>
			</persistent>
		</subscriptions>
	</telemetry-system>
	<aaa xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-lib-cfg">
		<usernames xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-locald-cfg">
			<username>
				<ordering-index>0</ordering-index>
				<name>vagrant</name>
				<usergroup-under-usernames>
					<usergroup-under-username>
						<name>root-lr</name>
					</usergroup-under-username>
					<usergroup-under-username>
						<name>cisco-support</name>
					</usergroup-under-username>
				</usergroup-under-usernames>
				<secret>$1$FzMk$Y5G3Cv0H./q0fG.LGyIJS1</secret>
			</username>
			<username>
				<ordering-index>1</ordering-index>
				<name>root</name>
				<usergroup-under-usernames>
					<usergroup-under-username>
						<name>root-lr</name>
					</usergroup-under-username>
					<usergroup-under-username>
						<name>cisco-support</name>
					</usergroup-under-username>
				</usergroup-under-usernames>
				<secret>$1$7kTu$zjrgqbgW08vEXsYzUycXw1</secret>
			</username>
		</usernames>
	</aaa>
	<interfaces xmlns="http://openconfig.net/yang/interfaces">
		<interface>
			<name>Loopback0</name>
			<config>
				<name>Loopback0</name>
				<type xmlns:idx="urn:ietf:params:xml:ns:yang:iana-if-type">idx:softwareLoopback</type>
				<enabled>true</enabled>
			</config>
			<subinterfaces>
				<subinterface>
					<index>0</index>
					<ipv4 xmlns="http://openconfig.net/yang/interfaces/ip">
						<addresses>
							<address>
								<ip>50.1.1.1</ip>
								<config>
									<ip>50.1.1.1</ip>
									<prefix-length>32</prefix-length>
								</config>
							</address>
						</addresses>
					</ipv4>
				</subinterface>
			</subinterfaces>
		</interface>
		<interface>
			<name>TenGigE0/0/0/1</name>
			<config>
				<name>TenGigE0/0/0/1</name>
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
			<name>TenGigE0/0/0/2</name>
			<config>
				<name>TenGigE0/0/0/2</name>
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
			<name>TenGigE0/0/0/3</name>
			<config>
				<name>TenGigE0/0/0/3</name>
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
			<name>TenGigE0/0/0/4</name>
			<config>
				<name>TenGigE0/0/0/4</name>
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
			<name>TenGigE0/0/0/5</name>
			<config>
				<name>TenGigE0/0/0/5</name>
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
			<name>TenGigE0/0/0/6</name>
			<config>
				<name>TenGigE0/0/0/6</name>
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
			<name>TenGigE0/0/0/7</name>
			<config>
				<name>TenGigE0/0/0/7</name>
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
			<name>TenGigE0/0/0/8</name>
			<config>
				<name>TenGigE0/0/0/8</name>
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
			<name>TenGigE0/0/0/9</name>
			<config>
				<name>TenGigE0/0/0/9</name>
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
			<name>TenGigE0/0/0/10</name>
			<config>
				<name>TenGigE0/0/0/10</name>
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
			<name>TenGigE0/0/0/11</name>
			<config>
				<name>TenGigE0/0/0/11</name>
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
			<name>TenGigE0/0/0/12</name>
			<config>
				<name>TenGigE0/0/0/12</name>
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
			<name>TenGigE0/0/0/13</name>
			<config>
				<name>TenGigE0/0/0/13</name>
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
			<name>TenGigE0/0/0/14</name>
			<config>
				<name>TenGigE0/0/0/14</name>
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
			<name>TenGigE0/0/0/15</name>
			<config>
				<name>TenGigE0/0/0/15</name>
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
			<name>TenGigE0/0/0/16</name>
			<config>
				<name>TenGigE0/0/0/16</name>
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
			<name>TenGigE0/0/0/17</name>
			<config>
				<name>TenGigE0/0/0/17</name>
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
			<name>TenGigE0/0/0/18</name>
			<config>
				<name>TenGigE0/0/0/18</name>
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
			<name>TenGigE0/0/0/19</name>
			<config>
				<name>TenGigE0/0/0/19</name>
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
			<name>TenGigE0/0/0/20</name>
			<config>
				<name>TenGigE0/0/0/20</name>
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
			<name>TenGigE0/0/0/21</name>
			<config>
				<name>TenGigE0/0/0/21</name>
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
			<name>TenGigE0/0/0/22</name>
			<config>
				<name>TenGigE0/0/0/22</name>
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
			<name>TenGigE0/0/0/23</name>
			<config>
				<name>TenGigE0/0/0/23</name>
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
			<name>TenGigE0/0/0/24</name>
			<config>
				<name>TenGigE0/0/0/24</name>
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
			<name>TenGigE0/0/0/25</name>
			<config>
				<name>TenGigE0/0/0/25</name>
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
			<name>TenGigE0/0/0/26</name>
			<config>
				<name>TenGigE0/0/0/26</name>
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
			<name>TenGigE0/0/0/27</name>
			<config>
				<name>TenGigE0/0/0/27</name>
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
			<name>TenGigE0/0/0/28</name>
			<config>
				<name>TenGigE0/0/0/28</name>
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
			<name>TenGigE0/0/0/29</name>
			<config>
				<name>TenGigE0/0/0/29</name>
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
			<name>TenGigE0/0/0/30</name>
			<config>
				<name>TenGigE0/0/0/30</name>
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
			<name>TenGigE0/0/0/31</name>
			<config>
				<name>TenGigE0/0/0/31</name>
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
			<name>TenGigE0/0/0/32</name>
			<config>
				<name>TenGigE0/0/0/32</name>
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
			<name>TenGigE0/0/0/33</name>
			<config>
				<name>TenGigE0/0/0/33</name>
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
			<name>TenGigE0/0/0/34</name>
			<config>
				<name>TenGigE0/0/0/34</name>
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
			<name>TenGigE0/0/0/35</name>
			<config>
				<name>TenGigE0/0/0/35</name>
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
			<name>TenGigE0/0/0/36</name>
			<config>
				<name>TenGigE0/0/0/36</name>
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
			<name>TenGigE0/0/0/37</name>
			<config>
				<name>TenGigE0/0/0/37</name>
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
			<name>TenGigE0/0/0/38</name>
			<config>
				<name>TenGigE0/0/0/38</name>
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
			<name>TenGigE0/0/0/39</name>
			<config>
				<name>TenGigE0/0/0/39</name>
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
			<name>TenGigE0/0/0/40</name>
			<config>
				<name>TenGigE0/0/0/40</name>
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
			<name>TenGigE0/0/0/41</name>
			<config>
				<name>TenGigE0/0/0/41</name>
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
			<name>TenGigE0/0/0/42</name>
			<config>
				<name>TenGigE0/0/0/42</name>
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
			<name>TenGigE0/0/0/43</name>
			<config>
				<name>TenGigE0/0/0/43</name>
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
			<name>TenGigE0/0/0/44</name>
			<config>
				<name>TenGigE0/0/0/44</name>
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
			<name>TenGigE0/0/0/45</name>
			<config>
				<name>TenGigE0/0/0/45</name>
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
			<name>TenGigE0/0/0/46</name>
			<config>
				<name>TenGigE0/0/0/46</name>
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
			<name>TenGigE0/0/0/47</name>
			<config>
				<name>TenGigE0/0/0/47</name>
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
			<name>HundredGigE0/0/1/0</name>
			<config>
				<name>HundredGigE0/0/1/0</name>
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
					<ipv4 xmlns="http://openconfig.net/yang/interfaces/ip">
						<addresses>
							<address>
								<ip>10.1.1.10</ip>
								<config>
									<ip>10.1.1.10</ip>
									<prefix-length>24</prefix-length>
								</config>
							</address>
						</addresses>
					</ipv4>
					<ipv6 xmlns="http://openconfig.net/yang/interfaces/ip">
						<config>
							<enabled>true</enabled>
						</config>
					</ipv6>
				</subinterface>
			</subinterfaces>
		</interface>
		<interface>
			<name>HundredGigE0/0/1/1</name>
			<config>
				<name>HundredGigE0/0/1/1</name>
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
					<ipv4 xmlns="http://openconfig.net/yang/interfaces/ip">
						<addresses>
							<address>
								<ip>11.1.1.10</ip>
								<config>
									<ip>11.1.1.10</ip>
									<prefix-length>24</prefix-length>
								</config>
							</address>
						</addresses>
					</ipv4>
					<ipv6 xmlns="http://openconfig.net/yang/interfaces/ip">
						<config>
							<enabled>true</enabled>
						</config>
					</ipv6>
				</subinterface>
			</subinterfaces>
		</interface>
		<interface>
			<name>MgmtEth0/RP0/CPU0/0</name>
			<config>
				<name>MgmtEth0/RP0/CPU0/0</name>
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
					<ipv4 xmlns="http://openconfig.net/yang/interfaces/ip">
						<addresses>
							<address>
								<ip>11.11.11.23</ip>
								<config>
									<ip>11.11.11.23</ip>
									<prefix-length>24</prefix-length>
								</config>
							</address>
						</addresses>
					</ipv4>
				</subinterface>
			</subinterfaces>
		</interface>
	</interfaces>
	<interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
		<interface-configuration>
			<active>act</active>
			<interface-name>Loopback0</interface-name>
			<interface-virtual></interface-virtual>
			<ipv4-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg">
				<addresses>
					<primary>
						<address>50.1.1.1</address>
						<netmask>255.255.255.255</netmask>
					</primary>
				</addresses>
			</ipv4-network>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/1</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/2</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/3</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/4</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/5</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/6</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/7</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/8</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/9</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/10</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/11</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/12</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/13</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/14</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/15</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/16</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/17</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/18</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/19</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/20</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/21</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/22</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/23</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/24</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/25</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/26</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/27</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/28</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/29</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/30</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/31</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/32</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/33</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/34</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/35</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/36</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/37</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/38</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/39</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/40</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/41</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/42</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/43</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/44</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/45</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/46</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>TenGigE0/0/0/47</interface-name>
			<shutdown></shutdown>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>HundredGigE0/0/1/0</interface-name>
			<ipv4-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg">
				<addresses>
					<primary>
						<address>10.1.1.10</address>
						<netmask>255.255.255.0</netmask>
					</primary>
				</addresses>
			</ipv4-network>
			<ipv6-neighbor xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv6-nd-cfg">
				<ra-unicast></ra-unicast>
			</ipv6-neighbor>
			<ipv6-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv6-ma-cfg">
				<addresses>
					<auto-configuration>
						<enable></enable>
					</auto-configuration>
				</addresses>
			</ipv6-network>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>HundredGigE0/0/1/1</interface-name>
			<ipv4-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg">
				<addresses>
					<primary>
						<address>11.1.1.10</address>
						<netmask>255.255.255.0</netmask>
					</primary>
				</addresses>
			</ipv4-network>
			<ipv6-neighbor xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv6-nd-cfg">
				<ra-unicast></ra-unicast>
			</ipv6-neighbor>
			<ipv6-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv6-ma-cfg">
				<addresses>
					<auto-configuration>
						<enable></enable>
					</auto-configuration>
				</addresses>
			</ipv6-network>
		</interface-configuration>
		<interface-configuration>
			<active>act</active>
			<interface-name>MgmtEth0/RP0/CPU0/0</interface-name>
			<ipv4-network xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg">
				<addresses>
					<primary>
						<address>11.11.11.23</address>
						<netmask>255.255.255.0</netmask>
					</primary>
				</addresses>
			</ipv4-network>
		</interface-configuration>
	</interface-configurations>
	<lacp xmlns="http://openconfig.net/yang/lacp">
		<interfaces>
			<interface>
				<name>Loopback0</name>
				<config>
					<name>Loopback0</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/1</name>
				<config>
					<name>TenGigE0/0/0/1</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/2</name>
				<config>
					<name>TenGigE0/0/0/2</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/3</name>
				<config>
					<name>TenGigE0/0/0/3</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/4</name>
				<config>
					<name>TenGigE0/0/0/4</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/5</name>
				<config>
					<name>TenGigE0/0/0/5</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/6</name>
				<config>
					<name>TenGigE0/0/0/6</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/7</name>
				<config>
					<name>TenGigE0/0/0/7</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/8</name>
				<config>
					<name>TenGigE0/0/0/8</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/9</name>
				<config>
					<name>TenGigE0/0/0/9</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/10</name>
				<config>
					<name>TenGigE0/0/0/10</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/11</name>
				<config>
					<name>TenGigE0/0/0/11</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/12</name>
				<config>
					<name>TenGigE0/0/0/12</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/13</name>
				<config>
					<name>TenGigE0/0/0/13</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/14</name>
				<config>
					<name>TenGigE0/0/0/14</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/15</name>
				<config>
					<name>TenGigE0/0/0/15</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/16</name>
				<config>
					<name>TenGigE0/0/0/16</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/17</name>
				<config>
					<name>TenGigE0/0/0/17</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/18</name>
				<config>
					<name>TenGigE0/0/0/18</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/19</name>
				<config>
					<name>TenGigE0/0/0/19</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/20</name>
				<config>
					<name>TenGigE0/0/0/20</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/21</name>
				<config>
					<name>TenGigE0/0/0/21</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/22</name>
				<config>
					<name>TenGigE0/0/0/22</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/23</name>
				<config>
					<name>TenGigE0/0/0/23</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/24</name>
				<config>
					<name>TenGigE0/0/0/24</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/25</name>
				<config>
					<name>TenGigE0/0/0/25</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/26</name>
				<config>
					<name>TenGigE0/0/0/26</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/27</name>
				<config>
					<name>TenGigE0/0/0/27</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/28</name>
				<config>
					<name>TenGigE0/0/0/28</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/29</name>
				<config>
					<name>TenGigE0/0/0/29</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/30</name>
				<config>
					<name>TenGigE0/0/0/30</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/31</name>
				<config>
					<name>TenGigE0/0/0/31</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/32</name>
				<config>
					<name>TenGigE0/0/0/32</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/33</name>
				<config>
					<name>TenGigE0/0/0/33</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/34</name>
				<config>
					<name>TenGigE0/0/0/34</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/35</name>
				<config>
					<name>TenGigE0/0/0/35</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/36</name>
				<config>
					<name>TenGigE0/0/0/36</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/37</name>
				<config>
					<name>TenGigE0/0/0/37</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/38</name>
				<config>
					<name>TenGigE0/0/0/38</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/39</name>
				<config>
					<name>TenGigE0/0/0/39</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/40</name>
				<config>
					<name>TenGigE0/0/0/40</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/41</name>
				<config>
					<name>TenGigE0/0/0/41</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/42</name>
				<config>
					<name>TenGigE0/0/0/42</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/43</name>
				<config>
					<name>TenGigE0/0/0/43</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/44</name>
				<config>
					<name>TenGigE0/0/0/44</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/45</name>
				<config>
					<name>TenGigE0/0/0/45</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/46</name>
				<config>
					<name>TenGigE0/0/0/46</name>
				</config>
			</interface>
			<interface>
				<name>TenGigE0/0/0/47</name>
				<config>
					<name>TenGigE0/0/0/47</name>
				</config>
			</interface>
			<interface>
				<name>HundredGigE0/0/1/0</name>
				<config>
					<name>HundredGigE0/0/1/0</name>
				</config>
			</interface>
			<interface>
				<name>HundredGigE0/0/1/1</name>
				<config>
					<name>HundredGigE0/0/1/1</name>
				</config>
			</interface>
			<interface>
				<name>MgmtEth0/RP0/CPU0/0</name>
				<config>
					<name>MgmtEth0/RP0/CPU0/0</name>
				</config>
			</interface>
		</interfaces>
	</lacp>
</config>
Testing the generated YANG XML by doing a merge config....
Successful!!
The CLI configuration created by applying the generated YANG XML is...


!! IOS XR Configuration version = 6.5.2.28I
logging console debugging
domain name cisco.com
username vagrant
 group root-lr
 group cisco-support
 secret 5 $1$FzMk$Y5G3Cv0H./q0fG.LGyIJS1
!
username root
 group root-lr
 group cisco-support
 secret 5 $1$7kTu$zjrgqbgW08vEXsYzUycXw1
!
address-family ipv4 unicast
!
interface Loopback0
 ipv4 address 50.1.1.1 255.255.255.255
!
interface MgmtEth0/RP0/CPU0/0
 ipv4 address 11.11.11.23 255.255.255.0
!
interface TenGigE0/0/0/1
 shutdown
!
interface TenGigE0/0/0/2
 shutdown
!
interface TenGigE0/0/0/3
 shutdown
!
interface TenGigE0/0/0/4
 shutdown
!
interface TenGigE0/0/0/5
 shutdown
!
interface TenGigE0/0/0/6
 shutdown
!
interface TenGigE0/0/0/7
 shutdown
!
interface TenGigE0/0/0/8
 shutdown
!
interface TenGigE0/0/0/9
 shutdown
!
interface TenGigE0/0/0/10
 shutdown
!
interface TenGigE0/0/0/11
 shutdown
!
interface TenGigE0/0/0/12
 shutdown
!
interface TenGigE0/0/0/13
 shutdown
!
interface TenGigE0/0/0/14
 shutdown
!
interface TenGigE0/0/0/15
 shutdown
!
interface TenGigE0/0/0/16
 shutdown
!
interface TenGigE0/0/0/17
 shutdown
!
interface TenGigE0/0/0/18
 shutdown
!
interface TenGigE0/0/0/19
 shutdown
!
interface TenGigE0/0/0/20
 shutdown
!
interface TenGigE0/0/0/21
 shutdown
!
interface TenGigE0/0/0/22
 shutdown
!
interface TenGigE0/0/0/23
 shutdown
!
interface TenGigE0/0/0/24
 shutdown
!
interface TenGigE0/0/0/25
 shutdown
!
interface TenGigE0/0/0/26
 shutdown
!
interface TenGigE0/0/0/27
 shutdown
!
interface TenGigE0/0/0/28
 shutdown
!
interface TenGigE0/0/0/29
 shutdown
!
interface TenGigE0/0/0/30
 shutdown
!
interface TenGigE0/0/0/31
 shutdown
!
interface TenGigE0/0/0/32
 shutdown
!
interface TenGigE0/0/0/33
 shutdown
!
interface TenGigE0/0/0/34
 shutdown
!
interface TenGigE0/0/0/35
 shutdown
!
interface TenGigE0/0/0/36
 shutdown
!
interface TenGigE0/0/0/37
 shutdown
!
interface TenGigE0/0/0/38
 shutdown
!
interface TenGigE0/0/0/39
 shutdown
!
interface TenGigE0/0/0/40
 shutdown
!
interface TenGigE0/0/0/41
 shutdown
!
interface TenGigE0/0/0/42
 shutdown
!
interface TenGigE0/0/0/43
 shutdown
!
interface TenGigE0/0/0/44
 shutdown
!
interface TenGigE0/0/0/45
 shutdown
!
interface TenGigE0/0/0/46
 shutdown
!
interface TenGigE0/0/0/47
 shutdown
!
interface HundredGigE0/0/1/0
 ipv4 address 10.1.1.10 255.255.255.0
 ipv6 nd unicast-ra
 ipv6 enable
!
interface HundredGigE0/0/1/1
 ipv4 address 11.1.1.10 255.255.255.0
 ipv6 nd unicast-ra
 ipv6 enable
!
router ospf 100
 router-id 50.1.1.1
 area 0
  interface Loopback0
   passive enable
  !
  interface HundredGigE0/0/1/0
   network point-to-point
  !
  interface HundredGigE0/0/1/1
   network point-to-point
  !
 !
!
telemetry model-driven
 sensor-group BGP
  sensor-path Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active
 !
 sensor-group BGPSession
  sensor-path Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/sessions
  sensor-path Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/process-info
 !
 sensor-group IPV6Neighbor
  sensor-path Cisco-IOS-XR-ipv6-nd-oper:ipv6-node-discovery/nodes/node/neighbor-interfaces/neighbor-interface/host-addresses/host-address
 !
 subscription IPV6
  sensor-group-id IPV6Neighbor sample-interval 15000
 !
 subscription BGP-FULL
  sensor-group-id BGP sample-interval 15000
 !
 subscription BGP-SESSION
  sensor-group-id BGPSession sample-interval 15000
 !
!
end


Input CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Finally resetting the router back to its original configuration
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
```



### Converting a Sample bgp configuration from CLI to YANG

The bgp CLI config in contention is:


```
cisco@ubuntu:~/cli2yang-tools$ cat bgp.config 
router bgp 65000
 bgp router-id 172.16.1.1
 address-family ipv4 unicast
 !
 neighbor-group IBGP
  remote-as 65000
  address-family ipv4 unicast
  update-source loopback0
  !
 !
 !
 neighbor 172.16.4.1
  remote-as 65000
  use neighbor-group IBGP
  address-family ipv4 unicast
  update-source loopback0
  !
 !
!
end  


```


Running the code first with the `-o` flag. This throws up an error during testing. But you do get the converted output in the logs.
When such an error occurs, the yang_nc.xml output file is not generated. Remove the `-t` flag to skip testing if you want the translated output anyhow.

```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c bgp.config -n 2201 -l 2221 -u vagrant -p vagrant -s 10.30.110.215 -t  -o
WARNING: not all XR platforms respond with Openconfig equivalent in GET requests but do respond with Native model formats. Also some Openconfig models have been in flux and testing the models sometimes fails. 
 If it works, try the -o flag along with the -t flag. If test fails, use the -o flag without the -t flag to atleast get the openconfig equivalent where possible. Else skip the -o flag altogether.
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
##################################################
YANG XML version of the input CLI configuration:
##################################################
<?xml version="1.0" encoding="utf-8"?>
<config>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65000</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>172.16.1.1</router-id>
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
										<as-yy>65000</as-yy>
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
									<neighbor-address>172.16.4.1</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65000</as-yy>
									</remote-as>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
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
	<network-instances xmlns="http://openconfig.net/yang/network-instance">
		<network-instance>
			<protocols>
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
									<index>##10.0.2.2##</index>
									<config>
										<index>##10.0.2.2##</index>
										<next-hop>10.0.2.2</next-hop>
									</config>
								</next-hop>
							</next-hops>
						</static>
					</static-routes>
				</protocol>
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
								<as>65000</as>
								<router-id>172.16.1.1</router-id>
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
									<peer-as>65000</peer-as>
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
								<neighbor-address>172.16.4.1</neighbor-address>
								<config>
									<neighbor-address>172.16.4.1</neighbor-address>
									<peer-as>65000</peer-as>
									<peer-group>IBGP</peer-group>
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
							</neighbor>
						</neighbors>
					</bgp>
				</protocol>
			</protocols>
		</network-instance>
	</network-instances>
</config>
Testing the generated YANG XML by doing a merge config....
Failed to merge required config over netconf, error: An expected element is missing.
<?xml version="1.0" encoding="utf-8"?>
<config>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65000</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>172.16.1.1</router-id>
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
										<as-yy>65000</as-yy>
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
									<neighbor-address>172.16.4.1</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65000</as-yy>
									</remote-as>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
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
	<network-instances xmlns="http://openconfig.net/yang/network-instance">
		<network-instance>
			<protocols>
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
									<index>##10.0.2.2##</index>
									<config>
										<index>##10.0.2.2##</index>
										<next-hop>10.0.2.2</next-hop>
									</config>
								</next-hop>
							</next-hops>
						</static>
					</static-routes>
				</protocol>
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
								<as>65000</as>
								<router-id>172.16.1.1</router-id>
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
									<peer-as>65000</peer-as>
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
								<neighbor-address>172.16.4.1</neighbor-address>
								<config>
									<neighbor-address>172.16.4.1</neighbor-address>
									<peer-as>65000</peer-as>
									<peer-group>IBGP</peer-group>
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
							</neighbor>
						</neighbors>
					</bgp>
				</protocol>
			</protocols>
		</network-instance>
	</network-instances>
</config>
Failed to merge configuration using generated XML files, check for error messages above...
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
```

Running the `-o` flag gives us a working output using the native XR model for BGP:



```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c bgp.config -n 2201 -l 2221 -u vagrant -p vagrant -s 10.30.110.215 -t 
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
##################################################
YANG XML version of the input CLI configuration:
##################################################
<?xml version="1.0" encoding="utf-8"?>
<config>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65000</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>172.16.1.1</router-id>
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
										<as-yy>65000</as-yy>
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
									<neighbor-address>172.16.4.1</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65000</as-yy>
									</remote-as>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
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
</config>
Testing the generated YANG XML by doing a merge config....
Successful!!
The CLI configuration created by applying the generated YANG XML is...


!! IOS XR Configuration version = 6.5.2.28I
router bgp 65000
 bgp router-id 172.16.1.1
 address-family ipv4 unicast
 !
 neighbor-group IBGP
  remote-as 65000
  update-source Loopback0
  address-family ipv4 unicast
  !
 !
 neighbor 172.16.4.1
  remote-as 65000
  use neighbor-group IBGP
  update-source Loopback0
  address-family ipv4 unicast
  !
 !
!
end


Input CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Finally resetting the router back to its original configuration

```

Finally dumping  the output:


```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ cat yang_nc.xml 
<?xml version="1.0" encoding="utf-8"?>
<config>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65000</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>172.16.1.1</router-id>
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
										<as-yy>65000</as-yy>
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
									<neighbor-address>172.16.4.1</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65000</as-yy>
									</remote-as>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
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
</config>
```




### Skipping the test flag


If you'd like an output when the test fails, just skip the `-t` flag. In the above examples, we do so with the openconfig BGP yang model.
This is useful to atleast understand what the openconfig model equivalent is before it may be massaged manually to make it work.



```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ ./cli2xmljson.py -b ncs5500_base.config -c bgp.config -n 2201 -l 2221 -u vagrant -p vagrant -s 10.30.110.215 -o
WARNING: not all XR platforms respond with Openconfig equivalent in GET requests but do respond with Native model formats. Also some Openconfig models have been in flux and testing the models sometimes fails. 
 If it works, try the -o flag along with the -t flag. If test fails, use the -o flag without the -t flag to atleast get the openconfig equivalent where possible. Else skip the -o flag altogether.
Replacing existing router configuration with the specified base_config using file:ncs5500_base.config
Establishing connection over netconf...
Fetching capabilities over netconf...
Fetching router's base configuration over netconf in YANG XML format...
Save original CLI configuration...
Apply (Merge Configuration) the provided input CLI file to the router's configuration
Fetch the changed configuration of the router using netconf in YANG XML format
Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...
Resetting the router configuration back to its original state...
##################################################
YANG XML version of the input CLI configuration:
##################################################
<?xml version="1.0" encoding="utf-8"?>
<config>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65000</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>172.16.1.1</router-id>
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
										<as-yy>65000</as-yy>
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
									<neighbor-address>172.16.4.1</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65000</as-yy>
									</remote-as>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
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
	<network-instances xmlns="http://openconfig.net/yang/network-instance">
		<network-instance>
			<protocols>
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
									<index>##10.0.2.2##</index>
									<config>
										<index>##10.0.2.2##</index>
										<next-hop>10.0.2.2</next-hop>
									</config>
								</next-hop>
							</next-hops>
						</static>
					</static-routes>
				</protocol>
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
								<as>65000</as>
								<router-id>172.16.1.1</router-id>
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
									<peer-as>65000</peer-as>
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
								<neighbor-address>172.16.4.1</neighbor-address>
								<config>
									<neighbor-address>172.16.4.1</neighbor-address>
									<peer-as>65000</peer-as>
									<peer-group>IBGP</peer-group>
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
							</neighbor>
						</neighbors>
					</bgp>
				</protocol>
			</protocols>
		</network-instance>
	</network-instances>
</config>
Testing the generated YANG XML by doing a merge config....
Input CLI configuration converted into YANG XML and saved in file: ./yang_nc.xml
Finally resetting the router back to its original configuration
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ 
```


Dump `yang_nc.xml` to view the final output.

```
cisco@ubuntu:~/cli2yang-tools$ 
cisco@ubuntu:~/cli2yang-tools$ cat yang_nc.xml 
<?xml version="1.0" encoding="utf-8"?>
<config>
	<bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg">
		<instance>
			<instance-name>default</instance-name>
			<instance-as>
				<as>0</as>
				<four-byte-as>
					<as>65000</as>
					<bgp-running></bgp-running>
					<default-vrf>
						<global>
							<router-id>172.16.1.1</router-id>
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
										<as-yy>65000</as-yy>
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
									<neighbor-address>172.16.4.1</neighbor-address>
									<remote-as>
										<as-xx>0</as-xx>
										<as-yy>65000</as-yy>
									</remote-as>
									<neighbor-group-add-member>IBGP</neighbor-group-add-member>
									<update-source-interface>Loopback0</update-source-interface>
									<neighbor-afs>
										<neighbor-af>
											<af-name>ipv4-unicast</af-name>
											<activate></activate>
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
	<network-instances xmlns="http://openconfig.net/yang/network-instance">
		<network-instance>
			<protocols>
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
									<index>##10.0.2.2##</index>
									<config>
										<index>##10.0.2.2##</index>
										<next-hop>10.0.2.2</next-hop>
									</config>
								</next-hop>
							</next-hops>
						</static>
					</static-routes>
				</protocol>
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
								<as>65000</as>
								<router-id>172.16.1.1</router-id>
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
									<peer-as>65000</peer-as>
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
								<neighbor-address>172.16.4.1</neighbor-address>
								<config>
									<neighbor-address>172.16.4.1</neighbor-address>
									<peer-as>65000</peer-as>
									<peer-group>IBGP</peer-group>
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
							</neighbor>
						</neighbors>
					</bgp>
				</protocol>
			</protocols>
		</network-instance>
	</network-instances>
</config>cisco@ubuntu:~/cli2yang-tools$ 


``` 
