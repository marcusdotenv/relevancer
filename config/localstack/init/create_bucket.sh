#!/bin/bash

wait_for_localstack() {
    echo "Waiting localstack..."
    while ! aws --endpoint-url=http://localstack:4566 s3api list-buckets > /dev/null 2>&1; do
        echo "Aguardando LocalStack estar pronto..."
        sleep 2
    done
    echo "LocalStack ready!!"
}


wait_for_localstack

echo "starting new bucket trie-bucket"
aws --endpoint-url=http://localstack:4566 s3api create-bucket --bucket trie-bucket

echo "loading to trie-bucket file default.json"
aws --endpoint-url=http://localstack:4566 s3 cp /etc/localstack/init/default.json s3://trie-bucket/
