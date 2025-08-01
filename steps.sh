docker image rm -f gsc-confidential-qloo-mcp-server gsc-confidential-qloo-mcp-server-unsigned confidential-qloo-mcp-server
docker build -t confidential-qloo-mcp-server .
cd docker/gsc
./gsc build -c ../confidential-qloo-mcp-server.config.yaml --rm confidential-qloo-mcp-server ../confidential-qloo-mcp-server.manifest
./gsc sign-image -c ../confidential-qloo-mcp-server.config.yaml  confidential-qloo-mcp-server "$HOME"/.config/gramine/enclave-key.pem
./gsc info-image gsc-confidential-qloo-mcp-server
cd ../../
docker run -p 8000:8000 --rm --env GRAMINE_MODE=direct \
    --security-opt seccomp=seccomp.json \
    gsc-confidential-qloo-mcp-server