import boto3
import os
from dotenv import load_dotenv
import botocore.exceptions

load_dotenv()

def download_s3_logs(bucket_name, download_path):
    try:
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)

        if not os.path.exists(download_path):
            os.makedirs(download_path)

        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                file_path = os.path.join(download_path, key)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                s3.download_file(bucket_name, key, file_path)
                print(f"Downloaded {key} to {file_path}")
    except botocore.exceptions.ClientError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    bucket_name = os.getenv('S3_BUCKET_NAME')
    download_path = os.getenv('DOWNLOAD_PATH')

    download_s3_logs(bucket_name, download_path)
