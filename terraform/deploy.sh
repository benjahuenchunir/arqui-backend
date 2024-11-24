#!/bin/bash

S3_BUCKET="iic2173-back-terraform"
ZIP_FILE="deploy.zip"
APPLICATION_NAME="iic2173-app-terraform"
DEPLOYMENT_GROUP_NAME="group-iic2173-terraform"

# Zip the artifact
zip -r $ZIP_FILE ../scripts/ ./appspec.yml ../docker-compose.production.yml ../.env

# Copy the zip file to S3
aws s3 cp $ZIP_FILE s3://$S3_BUCKET/$ZIP_FILE

aws deploy create-deployment \
  --application-name $APPLICATION_NAME \
  --deployment-group-name $DEPLOYMENT_GROUP_NAME \
  --region us-east-1 \
  --s3-location bucket=$S3_BUCKET,key=$ZIP_FILE,bundleType=zip \
  --file-exists-behavior OVERWRITE