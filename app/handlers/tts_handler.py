import os
import logging
import io
import boto3
from settings.nolo_config import NoloCFG


# Create Logger
logger = logging.getLogger(__name__)

# Load ENV data
cfg = NoloCFG()

# Load AWS Data
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# REGION_NAME = os.getenv("AWS_DEFAULT_REGION")

AWS_ACCESS_KEY_ID = cfg.aws_access_key_id
AWS_SECRET_ACCESS_KEY = cfg.aws_secret_access_key_id
REGION_NAME = cfg.aws_default_region

client = boto3.client(
    "polly",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
)


class NoloTTS:
    def __init__(self, audio_path=None, lang=None, prob=None):
        self.audio_path = f"{audio_path or os.getenv('OUT_TTS_PATH')}"
        self.ouput_exists = False
        self.lang = lang or "es"
        self.accuracy = prob or 0
        self.client = client

    def create_dir(self, doc_id: str) -> bool:
        try:
            if not os.path.exists(f"./{self.audio_path}/{doc_id}"):
                os.makedirs(f"./{self.audio_path}/{doc_id}")
            return True
        except Exception as e:
            print(e)
            return False

    def convert_to_tts(self, new_tts_file: dict) -> bool:
        """
        Convert text to audio in Memory
        """

        VoiceId = "Penelope" if new_tts_file["gender"] == "female" else "Miguel"

        response = client.synthesize_speech(
            VoiceId=VoiceId,
            OutputFormat="mp3",
            Text=new_tts_file.get("text_t_transform"),
            Engine="standard",
        )

        audio_stream = io.BytesIO(response["AudioStream"].read())
        logger.info("TTS Creation success!")

        return audio_stream
