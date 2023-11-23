import boto3
import os
from botocore.client import Config

from dotenv import load_dotenv

# Load ENV data
load_dotenv()

# Load AWS Data
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("AWS_DEFAULT_REGION")

client = boto3.client(
    "polly",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_ACCESS_KEY_ID,
    region_name=REGION_NAME,
)


class NoloTTS:
    def __init__(self, audio_path=None, lang=None, prob=None):
        self.audio_path = f"{audio_path or os.getenv('OUT_AUDIO_PATH')}"
        self.ouput_exists = False
        self.lang = lang or "es"
        self.accuracy = prob or 0

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
        Convert text to audio
        """

        # Create The Directory if not exists
        self.ouput_exists = self.create_dir(new_tts_file.get("doc_id"))

        if new_tts_file["gender"] == "female":
            VoiceId = "Penelope"
        else:
            VoiceId = "Miguel"

        filename = f"{new_tts_file.get('page_id')}_{new_tts_file.get('filename')}.mp3"
        response = client.synthesize_speech(
            VoiceId=VoiceId,
            OutputFormat="mp3",
            Text=new_tts_file.get("text_t_transform"),
            Engine="standard",
        )

        file_name = f"./{self.audio_path}/{self.hashed_name}/{filename}"

        with open(file_name, "wb") as tts:
            tts.write(response["AudioStream"].read())

        return True
