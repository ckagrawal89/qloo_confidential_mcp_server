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
gsc-confidential-qloo-mcp-server-unsigned confidential-qloo-mcp-server
docker build -t confidential-qloo-mcp-server .
cd docker/gsc
./gsc build -c ../confidential-qloo-mcp-server.config.yaml --rm confidential-qloo-mcp-server ../confidential-qloo-mcp-server.manifest
./gsc sign-image -c ../confidential-qloo-mcp-server.config.yaml  confidential-qloo-mcp-server "$HOME"/.config/gramine/enclave-key.pem
./gsc info-image gsc-confidential-qloo-mcp-server
```

### Starting Server in Direct Mode
```
docker run -p 8000:8000 --rm --entrypoint ""  --env GRAMINE_MODE=direct   --security-opt seccomp=seccomp.j
son   gsc-confidential-qloo-mcp-server   python -m src.qloo_mcp_server --isDev
```

The repetetive steps from above after building gramine_base and present in steps.sh and can be executed using:
```
bash steps.sh
```

## Starting Server on Secure Hardware
```
docker run --rm -it \
  --device=/dev/sgx_enclave \
  --device=/dev/sgx_provision \
  -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket \
  -p 8000:8000 \
  gsc-confidential-qloo-mcp-server
```
