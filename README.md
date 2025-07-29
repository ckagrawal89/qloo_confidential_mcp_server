# ➡️ confidential-mcp-server
<div align="center">

<strong>Confidential MCP server</strong>
</div>

## Overview

A Confidential MCP Server implementation running on [Gramine](https://github.com/gramineproject/gramine). It connects to your QLOO API to get insight.
  
## Dependencies
 - Intel SGX Hardware
 - Gramine
 - python 3.13
 - Ubuntu 22.04
 - Intel SGX SDK & PSW

## Initial Setup
Setup Venv:
```
python -m venv .venv
source .venv/bin/activate
```
Install Deps:
```
pip install .[dev]
```

## Local Development
```
python -m src.qloo_mcp_server --isDev 
```

## Production
First clone gsc:
```
git clone https://github.com/gramineproject/gsc docker/gsc
```
Then generate enclave private key:
```
gramine-sgx-gen-private-key
```
Build gramine base (just once):
```
./gsc build-gramine --rm --no-cache -c ../gramine_base.config.yaml gramine_base
```

### Image building, graminisation and signing
```
docker build -t confidential-mcp-server .
cd docker/gsc
./gsc build -c ../confidential-mcp-server.config.yaml --rm confidential-mcp-server ../confidential-mcp-server.manifest
./gsc sign-image -c ../confidential-mcp-server.config.yaml  confidential-mcp-server "$HOME"/.config/gramine/enclave-key.pem
./gsc info-image gsc-confidential-mcp-server
```

### Starting Server in Direct Mode
```
docker run -p 8000:8000 --rm --env GRAMINE_MODE=direct \
  --security-opt seccomp=seccomp.json \
  gsc-confidential-mcp-server
```

The repetetive steps from above after building gramine_base and present in steps.sh and can be executed using:
```
bash steps.sh
```

## Starting Server on Secure Hardware
```
docker run -itp --device=/dev/sgx_provision:/dev/sgx/provision  --device=/dev/sgx_enclave:/dev/sgx/enclave -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -p 8000:8000 --rm gsc-confidential-mcp-server
```
