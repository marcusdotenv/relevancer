#!/bin/bash

echo "Criando novo bucket"
aws --endpoint-url=http://localstack:4566 s3api create-bucket --bucket trie-bucket
