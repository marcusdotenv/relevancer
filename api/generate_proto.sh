#!/bin/sh
# Generates trie_pb2.py from trie.proto. The output is gitignored, so this
# must run before the API or the tests are started.
set -e

PROTO_DIR="$(dirname "$0")/src/infrastructure/adapters/impl/serializer/proto"

python -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$PROTO_DIR" \
    "$PROTO_DIR/trie.proto"
