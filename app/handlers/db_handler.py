import boto3
import os
from dotenv import load_dotenv
from botocore.client import Config
from botocore.exceptions import ClientError
import logging
from models.iam_model import User, UserInDB
from settings.nolo_config import NoloCFG



# Create Logger
logger = logging.getLogger(__name__)

# Load ENV data
# load_dotenv()
cfg = NoloCFG()

# Load AWS Env
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# REGION_NAME = os.getenv("AWS_DEFAULT_REGION")

AWS_ACCESS_KEY_ID = cfg.aws_access_key_id
AWS_SECRET_ACCESS_KEY = cfg.aws_secret_access_key_id
REGION_NAME = cfg.aws_default_region

# Global AWS Client
client = boto3.client(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
    # config=Config(signature_version="v4"),
)

resource = boto3.resource(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
    # config=Config(signature_version="v4"),
)


class NoloDBHandler:
    """
    Dynamo DB Handler for Nolo Reader
    """

    def __init__(self, table_name=None):
        self.table_name = table_name or os.getenv("API_DDB_TABLE_NAME")
        logger.info("NoloDBHandler Created")

    def get_table(self):
        """
        Connect to DDB and get access to the table
        """
        logger.info("NoloDBHandler Table Conn Created")
        return resource.Table(self.table_name)


class NoloUserDB:
    """
    User DB CRUD Operations
    """

    def __init__(self):
        self.user_db = os.getenv("USER_DDB_TABLE_NAME")
        self.table = resource.Table(self.user_db)
        logger.info("NoloUserDB Object Created")

    def get_one_user(self, username: str) -> UserInDB:
        table = self.table
        response = table.get_item(Key={"username": username})
        user = response.get("Item")

        if not user:
            logging.warning(f"No User {username} Object at DB")
            return None

        logger.info(f"User {username} Object Found ")
        return UserInDB(**user)

    def get_all_users(self) -> dict:
        table = self.table
        response = table.scan(
            ProjectionExpression="username, email, fullname, disabled"
        )
        data = response["Items"]

        logger.info(f"UserList Object Found ")
        return data

    def insert_user(self, user: User):
        table = self.table
        response = table.put_item(Item=user)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        logger.info(f"User {user.username} Object created ")
        return status_code

    def delete_user(self, username: str):
        table = self.table
        response = table.delete_item(Key={"username": username})
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]

        logger.info(f"User {username} Object deleted ")
        return status_code
