#!/bin/bash

echo "Criando novo bucket"
aws --endpoint-url=http://localstack:4566 s3api create-bucket --bucket trie-bucket
echo "Adicionando default trie"
aws --endpoint-url=http://localstack:4566 s3 cp /etc/localstack/init/default.json s3://trie-bucket/