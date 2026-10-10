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

echo "starting new bucket $TERM_FILE_STORAGE_BUCKET"
aws --endpoint-url=http://localstack:4566 s3api create-bucket --bucket "$TERM_FILE_STORAGE_BUCKET"

echo "loading to $TERM_FILE_STORAGE_BUCKET file $TERM_FILE_NAME"
aws --endpoint-url=http://localstack:4566 s3 cp "/etc/localstack/init/$TERM_FILE_NAME" "s3://$TERM_FILE_STORAGE_BUCKET/"
