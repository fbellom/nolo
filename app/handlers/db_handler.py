import boto3
import os
from dotenv import load_dotenv

from models.iam_model import User, UserInDB

# Load ENV data
load_dotenv()

# Load AWS Env
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("AWS_DEFAULT_REGION")

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


class NoloUserDB:
    """
    User DB CRUD Operations
    """

    def __init__(self):
        self.user_db = os.getenv("USER_DDB_TABLE_NAME")
        self.table = resource.Table(self.user_db)

    def get_one_user(self, username: str) -> UserInDB:
        table = self.table
        response = table.get_item(Key={"username": username})
        user = response.get("Item")

        if not user:
            return None

        return UserInDB(**user)

    def get_all_users(self) -> dict:
        table = self.table
        response = table.scan(
            ProjectionExpression="username, email, fullname, disabled"
        )
        data = response["Items"]

        return data

    def insert_user(self, user: User):
        table = self.table
        response = table.put_item(Item=user)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]

        return status_code

    def delete_user(self, username: str):
        table = self.table
        response = table.delete_item(Key={"username": username})
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]

        return status_code
