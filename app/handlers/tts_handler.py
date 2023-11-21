import boto3
import os
from botocore.client import Config

from dotenv import load_dotenv

# Load ENV data
load_dotenv()

# Load AWS Data
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("REGION_NAME")

client = boto3.client(
    "polly",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_ACCESS_KEY_ID,
    region_name=REGION_NAME,
)


class NoloCloudTTS:
    def __init__(self, audio_path=None, hashed_name=None, lang=None, prob=None):
        self.audio_path = f"{audio_path or os.getenv('OUT_AUDIO_PATH')}"
        self.hashed_name = hashed_name
        self.ouput_exists = self.create_dir()

    def create_dir(self) -> bool:
        try:
            if not os.path.exists(f"./{self.audio_path}/{self.hashed_name}"):
                os.makedirs(f"./{self.out_txt_path}/{self.hashed_name}")
            return True
        except Exception as e:
            print(e)
            return False
