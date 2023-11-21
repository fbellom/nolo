
import boto3
import os
from dotenv import load_dotenv

# Load ENV data
load_dotenv()

# Load AWS Env
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("REGION_NAME")

# Global AWS Client
client = boto3.client(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_ACCESS_KEY_ID,
    region_name=REGION_NAME,
)

resource = boto3.resource(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_ACCESS_KEY_ID,
    region_name=REGION_NAME,
)

class NoloDBHandler:
    """
    Dynamo DB Handler for Nolo Reader
    """

    def __init__(self, table_name=None):
        self.table_name = table_name or os.getenv("API_DDB_TABLE_NAME") 


    def get_table(self):
        """
        Connect to DDB and get access to the table
        """
        return resource.Table(self.table_name) 

    


