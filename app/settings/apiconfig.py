import os
from dotenv import load_dotenv

load_dotenv()

DESCRIPTION_DATA = """
NOLO API helps you manage Converted Documents to be displayed by NoloReader App
## Documents
CRUD DOcuments for Reader

## ETL
Handle the Adquisitions of new documents
"""
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")


class NoloCFG:
    """
    NOLO Initials Parameters
    """

    def __init__(self):
        self.title = "NOLO API Backend"
        self.description = DESCRIPTION_DATA
        self.version = f"1.0.0" or os.getenv("API_VERSION")
        self.secret_key = "" or os.getenv("SECRET_KEY")
        self.root_path = "" or os.getenv("API_ROOT_URI")
        self.run_mode = "" or os.getenv("API_RUN_MODE")
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key_id = AWS_SECRET_ACCESS_KEY
        self.aws_default_region = AWS_DEFAULT_REGION
