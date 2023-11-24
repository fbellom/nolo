import boto3
import logging
import os
from botocore.client import Config
from botocore.exceptions import ClientError
from settings.apiconfig import NoloCFG

# from dotenv import load_dotenv

# Load ENV data
# load_dotenv()
cfg = NoloCFG()

# Load AWS Data
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# REGION_NAME = os.getenv("AWS_DEFAULT_REGION")

AWS_ACCESS_KEY_ID = cfg.aws_access_key_id
AWS_SECRET_ACCESS_KEY = cfg.aws_secret_access_key_id
REGION_NAME = cfg.aws_default_region


# client = boto3.client(
#     "s3",
#     aws_access_key_id=AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=AWS_ACCESS_KEY_ID,
#     region_name=REGION_NAME,
# )


class NoloBlobAPI:
    """
    S3 Objects Handler
    """

    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or os.getenv("BUCKET_NAME")
        self.bucket = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION_NAME,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        logging.info(f"NoloBlob Object Created")

    def generate_presigned_url(self, filename, expires=3600):
        return self.bucket.generate_presigned_url(
            ClientMethod="get_object",
            ExpiresIn=expires,
            Params={"Bucket": self.bucket_name, "Key": filename},
        )

    def generate_presigned_post_fields(self, path_prefix="", expires=3600):
        return self.bucket.generate_presigned_post(
            self.bucket_name,
            path_prefix + "${filename}",
            ExpiresIn=expires,
        )

        """
            RETURNS : 
            {
                "fields": {...},
                "url": "https://s3.us-east-2.amazonaws.com/presigned-test"
            }
        """

    def get_files(self, path_prefix=""):
        object_list = self.bucket.list_objects(
            Bucket=self.bucket_name, Prefix=path_prefix
        )

        if "Contents" not in object_list:
            return []

        return [
            {
                "url": self.generate_presigned_url(file.get("Key")),
                "filename": file.get("Key"),
            }
            for file in object_list.get("Contents")
        ]

    def delete_file(self, filename):
        response = self.bucket.delete_object(Bucket=self.bucket_name, Key=filename)
        return response.get("DeleteMarker")

    def upload_file(self, filename, file_path):
        try:
            self.bucket.upload_file(filename, self.bucket_name, file_path)
            return True
        except ClientError as e:
            logging.error(e)
            return False

    def get_one_object(self, filename):
        try:
            response = self.bucket.get_object(Bucket=self.bucket_name, Key=filename)

            if response:
                return True
        except ClientError as e:
            logging.error(e)
            return False

    def delete_all_objects_from_s3_folder(self, prefix=None):
        """
        This function deletes all files in a folder from S3 bucket
        :return: True/False
        """

        try:
            # First we list all files in folder
            response = self.bucket.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            files_in_folder = response["Contents"]
            files_to_delete = []
            # We will create Key array to pass to delete_objects function
            for f in files_in_folder:
                files_to_delete.append({"Key": f["Key"]})

            # This will delete all files in a folder
            response = self.bucket.delete_objects(
                Bucket=self.bucket_name, Delete={"Objects": files_to_delete}
            )

            return True

        except ClientError as e:
            logging.error(e)
            return False
