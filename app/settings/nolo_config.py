import os
from dotenv import load_dotenv
import logging

load_dotenv()

DESCRIPTION_DATA = """
NOLO Booklet API helps you manage Converted Documents to be displayed by NoloReader App
## Reader
CRUD Documents for Reader

## Booklet
CRUD Proccess For files

"""
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")


# Set Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


class NoloCFG:
    """
    NOLO Initials Parameters
    """

    def __init__(self):
        self.title = "NOLO Booklet API Backend"
        self.description = DESCRIPTION_DATA
        self.version = "1.1.0" or os.getenv("API_VERSION")
        self.secret_key = "" or os.getenv("SECRET_KEY")
        self.root_path = "" or os.getenv("API_ROOT_URI")
        self.run_mode = "" or os.getenv("API_RUN_MODE")
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key_id = AWS_SECRET_ACCESS_KEY
        self.aws_default_region = AWS_DEFAULT_REGION
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_org_id = os.getenv("OPENAI_ORG_ID")
        self.openai_max_char = os.getenv("OPENAI_PROMPT_MAX_CHAR")
        self.openai_max_tkn = os.getenv("OPENAI_PROMPT_MAX_TKN")
        self.openai_min_lines = os.getenv("OPENAI_PROMPT_MIN_LINES")
        self.openai_model = "gpt-4-vision-preview" or os.getenv("OPENAI_MODEL")
        self.logs_cfg = logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s"
        )

        # inform
        logger.info("Nolo APP Config in Use", extra={"data": self})
