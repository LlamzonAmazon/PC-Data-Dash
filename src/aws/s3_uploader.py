import boto3
import os
from pathlib import Path
import yaml
from botocore.exceptions import ClientError, NoCredentialsError


class S3Uploader:
    def __init__(self, config_path="src/config/settings.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.bucket = self.config['aws']['s3']['bucket_name']
        self.region = self.config['aws']['s3']['region']
        self.s3_client = boto3.client('s3', region_name=self.region)
    
    def upload_file(self, local_path, s3_key=None):
        """Upload a single file to S3"""
        if s3_key is None:
            s3_key = str(Path(local_path)).replace('\\', '/')
        
        try:
            self.s3_client.upload_file(local_path, self.bucket, s3_key)
            print(f"✓ Uploaded {local_path} to s3://{self.bucket}/{s3_key}")
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"✗ Failed to upload {local_path}: {e}")
            return False
    
    def upload_directory(self, local_dir, s3_prefix=""):
        """Upload entire directory to S3"""
        local_path = Path(local_dir)
        if not local_path.exists():
            print(f"✗ Directory {local_dir} does not exist")
            return False
        
        success_count = 0
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}{relative_path}".replace('\\', '/')
                if self.upload_file(str(file_path), s3_key):
                    success_count += 1
        
        print(f"✓ Uploaded {success_count} files from {local_dir}")
        return success_count > 0

