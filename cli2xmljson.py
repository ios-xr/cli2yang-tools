#!/usr/bin/env python

import copy
import time, datetime
import subprocess
from deepdiff import DeepDiff 
import sys, os
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    import md5, sha
    from ncclient import manager

import logging
from lxml import etree
from xmldiff import main, formatting

from itertools import chain
from collections import OrderedDict

from functools import reduce  # forward compatibility for Python 3
import operator

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

def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)

def setInDict(dataDict, mapList, value):
    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

def changeInDict(dataDict, mapList, keyToChange, value):

    tempDict = dataDict
    try:
        for key in mapList:
            tempDict = tempDict[key]
    except KeyError:
        return {}

    tempDict[keyToChange] = value


def deleteKeysExcept(dataDict, allowedKey):
    keylist = list(dataDict.keys())
    for key in keylist:
        if str(key) != str(allowedKey):
          if '@xmlns' not in str(key):
            pop_result= dataDict.pop(key, None)
            if pop_result is None:
                print("Failed to pop key: ")
                print(key)
                return {}
    return dataDict

        
def getTreeFromDictPath(dataDict, pathList):
    parent_path_list = []
    parent_path_list.append(pathList[0])

    tempDict = OrderedDict()
    tempDict.update(dataDict)

    for path in pathList[1:]:
        deleteKeysExcept(getFromDict(dataDict, parent_path_list), path)
        parent_path_list.append(path)

    return dataDict


class YangCLIClient(object):
    def __init__(self,
                 host=None,
                 nc_port=None,
                 grpc_port=None,
                 xr_lnx_ssh_port=None,
                 cli_config_file=None,
                 base_config_file=None,
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


        if xr_lnx_ssh_port is None:
            print("Required parameter \"xr_lnx_ssh_port\" not specified, aborting")
            sys.exit(1)
        else:
            self.xr_lnx_ssh_port=xr_lnx_ssh_port

        if cli_config_file is None:
            print("Required parameter \"cli_config_file\" not specified, aborting")
            sys.exit(1)
        else:
            self.cli_config_file=cli_config_file

        if base_config_file is None:
            print("Required parameter \"base_config_file\" not specified, aborting")
            sys.exit(1)
        else:
            self.base_config_file = base_config_file
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
        self.grpc_getparam_list_base=[]
        self.grpc_getparam_list=[]
        
        self.grpc_json_base={}
        self.grpc_json={}
        
        self.nc_dict_base={}
        self.config_dict_base={}

        self.nc_dict={}
        self.config_dict={}

        self.netconf_diff = []
        self.grpc_diff = []

        self.original_config = ""
        
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.original_config_file = "./original_config_"+timestamp


        # Replace configuration with base config first

        print("Replacing existing router configuration with the specified base_config using file:"+str(self.base_config_file))

        xrreplace_output = self.cli_replace_config(config_file=self.base_config_file)
        if xrreplace_output["status"] == "error":
            print("Failed to replace base configuration of router before starting with file:")
            print(self.base_config_file)
            sys.exit(1)

        print("Establishing connection over netconf...")
        #establish netconf connection
        self.establish_nc_conn()

        if not self.netconf_only:
            #establish grpc connection
            self.establish_grpc_conn()


        print("Fetching capabilities over netconf...")
        # Fetch and store capabilities
        self.get_capabiities()


        print("Fetching router's base configuration over netconf in YANG XML format...")
        # Fetch config using netconf
        self.nc_get_config(dict_type="base")

        if not self.netconf_only:
            # Construct the parameters for gRPC
            self.construct_grpc_param_list(dict_type="base")

            #Construct grpc json data
            self.grpc_get_config(dict_type="base")

        
        print("Save original CLI configuration...")
        #First save original CLI config
        get_config = self.cli_show_command(show_cmd="show running-config")
        if get_config["status"] == "success":
            self.original_config = get_config["output"]
            #Now write this configuration to a known file location
            with open(self.original_config_file, 'w') as f:
                f.write(self.original_config)
        else:
            print("Failed to fetch original CLI configuration from the router")
            sys.exit(1)


        print("Apply (Merge Configuration) the provided input CLI file to the router's configuration")
        # Now Apply the CLI config        
        xrapply_output = self.cli_apply_config(config_file=self.cli_config_file)
        
        if xrapply_output["status"] == "error":
            print("Failed to apply input cli configuration via file")
            sys.exit(1)


        print("Fetch the changed configuration of the router using netconf in YANG XML format")
        # Fetch candidate
        self.nc_get_config(dict_type="candidate")

        if self.debug:
            print(xmltodict.unparse(self.nc_dict, pretty=True))

        if not self.netconf_only:
            # Construct the parameters for gRPC
            self.construct_grpc_param_list(dict_type="candidate")

            #Construct grpc json data
            self.grpc_get_config(dict_type="candidate")

    def run_bash(self, cmd=None):
        """User defined method in Child Class
           Wrapper method for basic subprocess.Popen to execute 
           bash commands on IOS-XR.
           :param cmd: bash command to be executed in XR linux shell. 
           :type cmd: str 
           
           :return: Return a dictionary with status and output
                    { 'status': '0 or non-zero', 
                      'output': 'output from bash cmd' }
           :rtype: dict
        """
        ## In XR the default shell is bash, hence the name
        if cmd is not None:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            out, err = process.communicate()
        else:
            print("No bash command provided")


        status = process.returncode

        return {"status" : status, "output" : out}





    def cli_show_command(self, show_cmd=None):
        if show_cmd is None:
            print("No bash command provided")
            return {"status" : "error", "output" : ""}

        ssh_cmd = "sshpass -p "+self.password+" ssh -o StrictHostKeyChecking=no -p "+self.xr_lnx_ssh_port+ " " +self.username+"@"+self.host+" \"sudo /bin/bash -c \'source /pkg/bin/ztp_helper.sh &&  xrcmd \\\""+show_cmd+"\\\" 2>/dev/null\'\""
        print ssh_cmd
        show_output = self.run_bash(cmd=ssh_cmd)

        if show_output["status"]:
            print("Failed to get the output of ssh_cmd")
            return {"status" : "error", "output" : ""}
        else:
            return {"status" : "success", "output" : show_output["output"]}





    def cli_apply_config(self, config_file=None):
        if config_file is None:
            print("No configuration file provided")
            return {"status" : "error", "output" : ""}


        #First transfer the config file to router

        filename = os.path.basename(config_file)

        transfer_file_cmd = "sshpass -p "+self.password+" scp -P "+self.xr_lnx_ssh_port+ " -o StrictHostKeyChecking=no  "+config_file+" "+self.username+"@"+self.host+":/misc/app_host/scratch/"+filename
        print transfer_file_cmd
        transfer_file = self.run_bash(transfer_file_cmd)

        if transfer_file["status"]:
            print("Failed to transfer configuration file to router")
            return {"status" : "error", "output" : ""}

        #Now apply
        ssh_cmd = "sshpass -p "+self.password+" ssh -o StrictHostKeyChecking=no -p "+self.xr_lnx_ssh_port+ " " +self.username+"@"+self.host+" \"sudo /bin/bash -c \'source /pkg/bin/ztp_helper.sh &&  xrapply /misc/app_host/scratch/"+filename+"\'\""

        print ssh_cmd
        xrapply_output = self.run_bash(cmd=ssh_cmd)
        
        if xrapply_output["status"]:
            print("Failed to get the output of ssh_cmd")
            return {"status" : "error", "output" : ""}
        else:
            #Fetch the last committed config
            last_commit = self.cli_show_command(show_cmd="show configuration commit changes last 1")
            if not last_commit["status"]:
                print(last_commit["output"])

            return {"status" : "success", "output" : xrapply_output["output"]}




    def cli_replace_config(self, config_file=None):
        if config_file is None:
            print("No configuration file provided")
            return {"status" : "error", "output" : ""}

        #First transfer the config file to router

        filename = os.path.basename(config_file)

        transfer_file_cmd = "sshpass -p "+self.password+" scp -P "+self.xr_lnx_ssh_port+ " -o StrictHostKeyChecking=no "+config_file+" "+self.username+"@"+self.host+":/misc/app_host/scratch/"+filename

        print transfer_file_cmd
        transfer_file = self.run_bash(transfer_file_cmd)

        if transfer_file["status"]:
            print("Failed to transfer configuration file to router")
            return {"status" : "error", "output" : ""}

        #Now replace 
        ssh_cmd = "sshpass -p "+self.password+" ssh -o StrictHostKeyChecking=no -p "+self.xr_lnx_ssh_port+ " " +self.username+"@"+self.host+" \"sudo /bin/bash -c \'source /pkg/bin/ztp_helper.sh &&  xrreplace /misc/app_host/scratch/"+filename+" \'\""

        print ssh_cmd            
        xrreplace_output = self.run_bash(cmd=ssh_cmd)

        if xrreplace_output["status"]:
            print("Failed to get the output of ssh_cmd")
            return {"status" : "error", "output" : ""}
        else:
            #Fetch the last committed config
            last_commit = self.cli_show_command(show_cmd="show configuration commit changes last 1")
            if not last_commit["status"]:
                print(last_commit["output"])

            return {"status" : "success", "output" : xrreplace_output["output"]}





    def list_diff(self, protocol=None):
        if protocol is None:
            print("Specify the protocol for which diff is desired - \"grpc\" or \"netconf\"")
            sys.exit(1)

        if (protocol == "grpc"):
           # base = self.grpc_json_base
           # candidate = self.grpc_json

           # s = set(candidate.keys())
           # self.grpc_diff = [x for x in  base.keys() if x not in s]
           #self.grpc_diff
           print "Skipping.."
        elif (protocol == "netconf"):
           base = self.nc_dict_base
           candidate = self.nc_dict

           self.netconf_diff = DeepDiff(base, candidate, ignore_order=True)
 
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
            

    def nc_get_config(self, dict_type=None):
        if dict_type is None:
            print("Dictionary type not specified - specify \"base\" or \"candidate\", aborting...")
            sys.exit(1)
        try:        
            response=self.conn.get_config(source="running")
            response_dict=xmltodict.parse(str(response))
            if (dict_type == "base"):
                self.config_dict_base=response_dict['rpc-reply']['data']
                for key in list(self.config_dict.keys()):
                    if key in self.skip_model:
                        self.config_dict_base.pop(key)
                self.nc_dict_base.update({"config" : self.config_dict_base})
            elif (dict_type == "candidate"):
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

    def construct_grpc_param_list(self, dict_type=None):
        if dict_type is None:
            print("Dictionary type not specified - specify \"base\" or \"candidate\", aborting...")
            sys.exit(1)
        try:
            if (dict_type == "base"):
                for key in list(self.config_dict_base.keys()):
                    if isinstance(self.config_dict_base[key], list):
                        for idx,item in enumerate(self.config_dict_base[key]):
                            if "@xmlns" in list(item.keys()):
                                if item["@xmlns"] in list(self.model_url_name_map.keys()):
                                    yangpath= self.model_url_name_map[item["@xmlns"]]["module"][0]
                                    self.grpc_getparam_list_base.append(yangpath+":"+key)
                                else:
                                    self.config_dict_base[key].pop(idx)
                    else:
                        if self.config_dict_base[key]["@xmlns"] in list(self.model_url_name_map.keys()):
                            if "@xmlns" in list(self.config_dict_base[key].keys()):
                                yangpath=self.model_url_name_map[self.config_dict_base[key]["@xmlns"]]["module"][0]
                                self.grpc_getparam_list_base.append(yangpath+":"+key)
                        else:
                            self.config_dict_base.pop(key)
            elif (dict_type == "candidate"):
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
                   
    def grpc_get_config(self, dict_type=None):
        if dict_type is None:
           print("Dictionary type not specified - specify \"base\" or \"candidate\", aborting...")
           sys.exit(1)

        if (dict_type == "base"): 
            for pathyang in self.grpc_getparam_list_base:
                path = '{"'+pathyang+'": [null]}'
                try:
                    err, result = self.grpc_client.getconfig(path)
                    if err:
                        print(err)
                        sys.exit(1)
                    self.grpc_json_base.update(json.loads(result))    
                except Exception as e:
                    print(
                        'Unable to perform gRPC get_config'
                        )
                    sys.exit(1)

        elif (dict_type == "candidate"):
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

    def write_nc_xml_to_file(self, filepath, dict_type=None):
        if dict_type is None:
            print("Specify dict type before writing xml to file, options: \"base\" or \"candidate\", aborting")
            sys.exit(1)

        with open(filepath, 'w') as yang_xml_fd:
            if (dict_type == "base"):
                yang_xml_fd.write(xmltodict.unparse(self.nc_dict_base, pretty=True))
            elif (dict_type == "candidate"):
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
                        help='gRPC port -- IMPORTANT: Not supported in this version. Support using GNMI will be brought in soon.')
        parser.add_argument('-l', '--xr-lnx-ssh-port', action='store', dest='xr_lnx_ssh_port',
                        help='XR linux shell SSH port')
        parser.add_argument('-u', '--username', action='store', dest='username',
                        help='IOS-XR AAA username')
        parser.add_argument('-p', '--password', action='store', dest='password',
                        help='IOS-XR AAA password')
        parser.add_argument('-c', '--input-cli-file', action='store', dest='input_cli_file',
                        help='Specify input file path for CLI configuration to convert into netconf RPC ')
        parser.add_argument('-b', '--base-config-file', action='store', dest='base_config_file',
                        help='Specify file path for base CLI configuration to apply to device before starting, by default: ./base.config')
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
             results.xr_lnx_ssh_port or
             results.input_cli_file or
             results.base_config_file or
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

    if results.nc_xml_file:
        nc_xml_file=results.nc_xml_file
    else:
        nc_xml_file='./yang_nc.xml'

    if results.grpc_json_file:
        grpc_json_file=results.grpc_json_file
    else:
        grpc_json_file='./yang_grpc.json'


    if results.base_config_file:
        base_config_file=results.base_config_file
    else:
        base_config_file='./base.config'
        
    client=YangCLIClient(host=results.host,
                         nc_port=results.nc_port,
                         grpc_port=results.grpc_port,
                         xr_lnx_ssh_port=results.xr_lnx_ssh_port,
                         cli_config_file=results.input_cli_file,
                         base_config_file=base_config_file,
                         username=results.username,
                         password=results.password,
                         debug=results.debug)  


    print("Determining diff between original YANG XML (base config) and current YANG XML (input CLI config)...")
    client.list_diff(protocol="netconf")

    print("Resetting the router configuration back to its original state...")
    #Finally rewrite original configuration of the device
    client.cli_replace_config(client.original_config_file)

    xml_dict = OrderedDict()



    if 'dictionary_item_added' in client.netconf_diff:
        dict_items = list(client.netconf_diff['dictionary_item_added'])

        for item in dict_items:
            item_keys = item[item.startswith("root") and len("root"):]
            item_keys = item_keys.strip('[]').replace('][',',')
            item_key_list = item_keys.split(',')
            item_key_list = [i.replace('\'', '') for i in item_key_list]
          
            dict_to_modify = copy.deepcopy(client.nc_dict)
            diff_dict = OrderedDict([(item_key_list[-1], getFromDict(client.nc_dict, item_key_list))])
            #diff_dict.update(getTreeFromDictPath(dict_to_modify, item_key_list))

            dict_path = OrderedDict()
            dict_path.update(getTreeFromDictPath(dict_to_modify, item_key_list))

            xml_dict.update(dict_path['config'])


    if 'iterable_item_added' in client.netconf_diff:
        iterable_items = list(client.netconf_diff['iterable_item_added'])
        iterable_dict = OrderedDict()
        list_dict = {}

        for item in iterable_items:
            item_keys = item[item.startswith("root") and len("root"):]
            item_keys = item_keys.strip('[]').replace('][',',')
            item_key_list = item_keys.split(',')
            item_key_list = [i.replace('\'', '') for i in item_key_list]

            list_dict.update({('_').join(item_key_list[:-1]): [] })
      
        for item in iterable_items:
            item_keys = item[item.startswith("root") and len("root"):]
            item_keys = item_keys.strip('[]').replace('][',',')
            item_key_list = item_keys.split(',')
            item_key_list = [i.replace('\'', '') for i in item_key_list]

            list_index = item_key_list[-1]
            item_key_list = item_key_list[:-1]
        
            fetch_list = list(getFromDict(client.nc_dict, item_key_list))
            diff_element = fetch_list[int(list_index)]
            list_dict[('_').join(item_key_list)].append(diff_element)
  
            dict_to_modify = copy.deepcopy(client.nc_dict)
   
            iterable_dict.update(getTreeFromDictPath(dict_to_modify, item_key_list))

            changeInDict(iterable_dict, item_key_list[:-1], item_key_list[-1], list_dict[('_').join(item_key_list)])
            xml_dict.update(iterable_dict['config'])


    if 'values_changed' in client.netconf_diff:
        values_dict = OrderedDict()
        values_changed = client.netconf_diff['values_changed']

        for item in values_changed:
            item_keys = item[item.startswith("root") and len("root"):]
            item_keys = item_keys.strip('[]').replace('][',',')
            item_key_list = item_keys.split(',')
            item_key_list = [i.replace('\'', '') for i in item_key_list]

            dict_to_modify = copy.deepcopy(client.nc_dict)
            values_dict.update(getTreeFromDictPath(dict_to_modify, item_key_list))

            xml_dict.update(values_dict['config'])


    if 'type_changes' in client.netconf_diff:
        values_dict = OrderedDict()

        for item in client.netconf_diff['type_changes']:
            new_item_type = client.netconf_diff['type_changes'][item]['new_type'] 
            new_item_value = client.netconf_diff['type_changes'][item]['new_value'] 

            item_keys = item[item.startswith("root") and len("root"):]
            item_keys = item_keys.strip('[]').replace('][',',')
            item_key_list = item_keys.split(',')
            item_key_list = [i.replace('\'', '') for i in item_key_list]

            
            dict_to_modify = copy.deepcopy(client.nc_dict)
            setInDict(dict_to_modify, item_key_list, new_item_value)

            values_dict.update(getTreeFromDictPath(dict_to_modify, item_key_list))

            xml_dict.update(values_dict['config'])


   
    xml_dict = OrderedDict([('config', xml_dict)]) 
    if client.debug:
        print("##################################################")
        print("YANG XML version of the input CLI configuration:")
        print("##################################################")
        print(xmltodict.unparse(xml_dict, pretty=True))


    print("Testing the generated YANG XML by doing a merge config....")
    if results.test:
        if not client.nc_config_merge(xmltodict.unparse(xml_dict, pretty=True).encode('utf-8')):
            print("Successful!!")
            print("The CLI configuration created by applying the generated YANG XML is...\n\n")
            print(str(client.cli_show_command(show_cmd="show configuration commit changes last 1")["output"]))
        else:
            print("Failed to merge configuration using generated XML files, check for error messages above...")
            sys.exit(1)

    filepath = nc_xml_file
    print("Input CLI configuration converted into YANG XML and saved in file: "+str(filepath))            
    with open(filepath, 'w') as yang_xml_fd:
        yang_xml_fd.write(xmltodict.unparse(xml_dict, pretty=True))
    
    with open('./yang_nc_base.xml', 'w') as yang_xml_fd:
        yang_xml_fd.write(xmltodict.unparse(client.nc_dict_base, pretty=True))

    with open('./yang_nc_get.xml', 'w') as yang_xml_fd:
        yang_xml_fd.write(xmltodict.unparse(client.nc_dict, pretty=True))



    print("Finally resetting the router back to its original configuration")
    client.cli_replace_config(config_file=client.original_config_file)

    os.remove(client.original_config_file)


