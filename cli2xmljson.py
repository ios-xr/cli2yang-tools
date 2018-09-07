#!/usr/bin/env python
import time

import sys, os, warnings
warnings.simplefilter("ignore", DeprecationWarning)
from ncclient import manager
import logging
from lxml import etree
import json
import xmltodict
from pprint import pprint
import pdb
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
     from urlparse import urlparse, parse_qs

import argparse

sys.path.append("./iosxr_grpc")
from cisco_grpc_client import CiscoGRPCClient

class YangCLIClient(object):
    def __init__(self,
                 host=None,
                 nc_port=None,
                 grpc_port=None,
                 username=None,
                 password=None,
                 debug=None,
                 device_params=None):
        
        self.netconf_only=False
        if host is None:
            print("Required parameter \"host\" not specified, aborting")
            sys.exit(1)
        else:
            self.host=host

        if nc_port is None:
            print("Required parameter \"nc_port\" not specified, aborting")
            sys.exit(1)
        else:
            self.nc_port=nc_port

        if grpc_port is None:
            self.netconf_only=True        
        else:
            self.grpc_port=grpc_port

        if username is None:
            print("Required parameter \"username\" not specified, aborting")
            sys.exit(1)
        else:
            self.username=username

        if password is None:
            print("Required parameter \"password\" not specified, aborting")
            sys.exit(1)
        else:
            self.password=password


        if device_params is None:
            self.device_params={'name':'iosxr'}
        else:
            self.device_params=device_params

        if debug is None:
            self.debug=False
        else:
            self.debug=debug

        self.model_url_name_map={}

        self.skip_model=['sdr-config', 'private-sdr']
        self.grpc_getparam_list=[]
        self.grpc_json={}
        self.nc_dict={}
        self.config_dict={}

        #establish netconf connection
        self.establish_nc_conn()

        if not self.netconf_only:
            #establish grpc connection
            self.establish_grpc_conn()

        # Fetch and store capabilities
        self.get_capabiities()

        # Fetch config using netconf
        self.nc_get_config()

        if not self.netconf_only:
            # Construct the parameters for gRPC
            self.construct_grpc_param_list()

            #Construct grpc json data
            self.grpc_get_config()

 
    def establish_nc_conn(self):
        try:
            self.conn = manager.connect(host=self.host,
                                   port=self.nc_port, 
                                   username=self.username, 
                                   password=self.password,
                                   device_params=self.device_params,
                                   hostkey_verify=False,
                                   look_for_keys=False, 
                                   allow_agent=False)
        except Exception as e:
            print("Failed to establish netconf connection, error: "+str(e))
            sys.exit(1)
        

    def get_capabiities(self):
        for capability in self.conn.server_capabilities:
            model_details=parse_qs(urlparse(capability).query, keep_blank_values=True)
            if urlparse(capability).netloc == "tail-f.com":
                continue    
            model_uri=urlparse(capability).scheme+"://"+urlparse(capability).netloc+urlparse(capability).path
            self.model_url_name_map.update({model_uri : model_details})
            

    def nc_get_config(self):
        try:        
            response=self.conn.get_config(source="running")
            response_dict=xmltodict.parse(str(response))
            self.config_dict=response_dict['rpc-reply']['data']
            for key in list(self.config_dict.keys()):
                if key in self.skip_model:
                    self.config_dict.pop(key)
            self.nc_dict.update({"config" : self.config_dict})

        except Exception as e:
            print("Failed to get running config, error: "+str(e))
            sys.exit(1)

    def nc_config_merge(self, data):
        try:
            nc_edit_config=self.conn.edit_config(data, 
                                    format='xml', target='candidate',
                                    default_operation='merge')
            self.conn.commit()
            return 0
        except Exception as e:
            print("Failed to merge required config over netconf, error: "+str(e))
            print(data)
            return 1 


    def establish_grpc_conn(self):
        try:
            self.grpc_client = CiscoGRPCClient(self.host, 
                                               self.grpc_port, 
                                               60,
                                               self.username,
                                               self.password)
        except Exception as e:
            print("Failed to connect to gRPC server on router, errot: "+str(e))
            sys.exit(1)

    def construct_grpc_param_list(self):
        try:
            for key in list(self.config_dict.keys()):
                if isinstance(self.config_dict[key], list):
                    for idx,item in enumerate(self.config_dict[key]):
                        if "@xmlns" in list(item.keys()):
                            if item["@xmlns"] in list(self.model_url_name_map.keys()):
                                yangpath= self.model_url_name_map[item["@xmlns"]]["module"][0]
                                self.grpc_getparam_list.append(yangpath+":"+key)
                            else:
                                self.config_dict[key].pop(idx)
                else:
                    if self.config_dict[key]["@xmlns"] in list(self.model_url_name_map.keys()):
                        if "@xmlns" in list(self.config_dict[key].keys()):
                            yangpath=self.model_url_name_map[self.config_dict[key]["@xmlns"]]["module"][0]
                            self.grpc_getparam_list.append(yangpath+":"+key)
                    else:
                        self.config_dict.pop(key)

        except Exception as e:
            print("Failed to extract gRPC params, error: "+str(e))
            sys.exit(1)
                   
    def grpc_get_config(self):
        for pathyang in self.grpc_getparam_list:
            path = '{"'+pathyang+'": [null]}'
            try:
                err, result = self.grpc_client.getconfig(path)
                if err:
                    print(err)
                    sys.exit(1)
                self.grpc_json.update(json.loads(result))    
            except Exception as e:
                print(
                    'Unable to perform gRPC get_config'
                    )
                sys.exit(1)



    def grpc_config_merge(self, data, retry=3, interval=150):
        if not self.netconf_only:
            count=0
            result=False
            while (count < retry):
               try:
                    response = self.grpc_client.mergeconfig(data)
                    if response.errors:
                        err = json.loads(response.errors)
                        print("Failed to merge configuration via gRPC, error: "+str(err))
                        result=False
                        count=count+1
                        time.sleep(interval)
                        continue
                    result=True 
                    break
               except Exception as e:
                    print(
                        'Failed to merge configuration via gRPC, error:'+str(e)
                        )
                    result=False
               count=count+1
               time.sleep(interval)
   
            if not result: 
                print(data)
            return result
        else:
            if self.debug:
                print("Skipping gRPC config merge since gRPC port wasn't specified")

    def grpc_check_last_cli_commit(self):
        if not self.netconf_only:
            try:  
                last_commit="show configuration commit list 1 detail"
                response = self.grpc_client.showcmdtextoutput(last_commit)

                for line in response:
                    print(line)

                last_commit_changes="show configuration commit changes last 1"
                response = self.grpc_client.showcmdtextoutput(last_commit_changes)
                for line in response:
                    print(line)
            except Exception as e:
                print("Failed to fetch last commit data, error:"+str(e))
                sys.exit(1)
        else:
            if self.debug:
                print("Skipping gRPC last cli commit check since gRPC port wasn't specified")

    def write_nc_xml_to_file(self, filepath):
        with open(filepath, 'w') as yang_xml_fd:
            yang_xml_fd.write(xmltodict.unparse(self.nc_dict, pretty=True))
        print("Router's CLI configuration converted into YANG XML and saved in file: "+str(filepath))

    def write_grpc_json_to_file(self, filepath):
        if not self.netconf_only:
            with open(filepath, 'w') as yang_json_fd:
                yang_json_fd.write(json.dumps(self.grpc_json, indent=4))
            print("Router's CLI configuration converted into YANG JSON and saved in file: "+str(filepath))
        else:
            if self.debug:
                print("Skipping gRPC file creation since gRPC port wasn't specified")
            

if __name__ == '__main__':

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--server', action='store', dest='host',
                          help='IP address of netconf server and gRPC server on the router')
        parser.add_argument('-n', '--netconf-port', action='store', dest='nc_port',
                        help='netconf port')
        parser.add_argument('-g', '--grpc-port', action='store', dest='grpc_port',
                        help='gRPC port')
        parser.add_argument('-u', '--username', action='store', dest='username',
                        help='IOS-XR AAA username')
        parser.add_argument('-p', '--password', action='store', dest='password',
                        help='IOS-XR AAA password')
        parser.add_argument('-d', '--debug', action='store_true', dest='debug',
                        help='Enable debugging')
        parser.add_argument('-t', '--test-merge', action='store_true', dest='test',
                        help='Test config merge with each output file')
        parser.add_argument('-x', '--nc-xml-file', action='store', dest='nc_xml_file',
                        help='Specify output file path for netconf based XML output ')
        parser.add_argument('-j', '--grpc-json-file', action='store', dest='grpc_json_file',
                        help='Specify output file path for gRPC based JSON output')

    except SystemExit:
        print("Invalid arguments provided, Error: " + str(sys.exc_info()[1]))
        parser.print_help()

    
    results = parser.parse_args()

    if not ( results.host or 
             results.nc_port or
             results.grpc_port or
             results.username or
             results.password or
             results.debug or
             results.test):
        parser.print_help()
        sys.exit(0)

    if results.debug:
        rootLogger = logging.getLogger('ncclient.transport.session')
        rootLogger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        rootLogger.addHandler(handler)        
        
    client=YangCLIClient(host=results.host,
                         nc_port=results.nc_port,
                         grpc_port=results.grpc_port,
                         username=results.username,
                         password=results.password,
                         debug=results.debug)  



    if results.nc_xml_file:
        nc_xml_file=results.nc_xml_file
    else:
        nc_xml_file='./yang_nc.xml'

    if results.grpc_json_file:
        grpc_json_file=results.grpc_json_file
    else:
        grpc_json_file='./yang_grpc.json'

    client.write_nc_xml_to_file(nc_xml_file)
    client.write_grpc_json_to_file(grpc_json_file)



    if results.test:
        # Test nc
        with open(nc_xml_file, 'r') as yang_nc:
            data=yang_nc.read()
        if not client.nc_config_merge(data):
            client.grpc_check_last_cli_commit()

        # Test grpc 
        with open(grpc_json_file, 'r') as yang_grpc:
            data=yang_grpc.read()
        if client.grpc_config_merge(data):
            client.grpc_check_last_cli_commit()


