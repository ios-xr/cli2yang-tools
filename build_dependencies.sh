#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${0}")"; echo "$(pwd)")"
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as sudo"
    echo "Please run the script as : sudo <scriptpath>"
    exit
fi

apt-get update && apt-get install -y python-pip python3-pip && \
        pip2 install --upgrade pip && \
            pip3 install --upgrade pip

pip2 install -r ${SCRIPT_DIR}/requirements_pip2.txt
pip3 install -r ${SCRIPT_DIR}/requirements_pip3.txt


# Removing old bindings
if [ -d ${SCRIPT_DIR}/iosxr_grpc/genpy ]; then
  rm -rf ${SCRIPT_DIR}/iosxr_grpc/genpy
fi

printf "Generating Python bindings..."
mkdir -p ${SCRIPT_DIR}/iosxr_grpc/genpy


cd ${SCRIPT_DIR}/iosxr_grpc/bigmuddy-network-telemetry-proto/proto_archive

for dir in `find . -type d -links 2`; do
  if [[ $dir = *"mdt_grpc_dialin"* ]];then
      set -x
      python -m grpc_tools.protoc -I ./ --python_out=${SCRIPT_DIR}/iosxr_grpc/genpy --grpc_python_out=${SCRIPT_DIR}/iosxr_grpc/genpy $dir/*.proto
      mkdir -p ${SCRIPT_DIR}/iosxr_grpc/genpy/$dir 
      touch ${SCRIPT_DIR}/iosxr_grpc/genpy/${dir}/__init__.py
      2to3 -w ${SCRIPT_DIR}/iosxr_grpc/genpy/*.py >/dev/null 2>&1
      set +x
  fi
done

for proto_file in *.proto; do
  set -x
  python -m grpc_tools.protoc -I ./ --python_out=${SCRIPT_DIR}/iosxr_grpc/genpy --grpc_python_out=${SCRIPT_DIR}/iosxr_grpc/genpy $proto_file
  2to3 -w ${SCRIPT_DIR}/iosxr_grpc/genpy/*.py >/dev/null 2>&1 
  touch ${SCRIPT_DIR}/iosxr_grpc/genpy/__init__.py
  set +x
done

echo "Done"
