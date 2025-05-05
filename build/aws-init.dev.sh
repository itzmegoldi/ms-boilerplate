#!/bin/bash
awslocal s3api create-bucket --bucket test-bucket
echo "this is amazing" > /tmp/my_file.txt 
awslocal s3api create-bucket --bucket mpw-app
awslocal s3 cp testdata/prod s3://mpw-app/prod/ --recursive
awslocal s3api put-object --bucket test-bucket --key my_file.txt --body /tmp/my_file.txt --content-type text/plain
awslocal sqs create-queue --queue-name test-queue --region us-east-1