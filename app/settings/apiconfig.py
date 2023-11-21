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


class NOLOConfig:
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
