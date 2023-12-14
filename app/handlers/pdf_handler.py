import time
import io
import os
import hashlib
from pdf2image import convert_from_bytes
import fitz
import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException
from handlers.s3_handler import NoloBlobAPI
from handlers.tts_handler import NoloTTS
from handlers.ai_handler import NoloAIHelper
from utils.text_cleaner import NoloCleaner
import logging
import shutil

# Create Logger
logger = logging.getLogger(__name__)

# Utils Import
cleaner = NoloCleaner()
polly = NoloTTS()
tts_client = polly.client
noloai = NoloAIHelper()


class NoloPDFHandler:
    """
    Class to Manage Files Conversion
    """

    def __init__(
        self, file_name=None, path=None, out_path=None, img_dpi=72, description=None
    ):
        self.fname = file_name or os.getenv("PDF_FILE")
        self.description = description or ""
        self.path = f"{path or os.getenv('PDF_PATH')}/{self.fname}"
        self.out_txt_path = f"{out_path or os.getenv('OUT_TXT_PATH')}"
        self.out_img_path = f"{out_path or os.getenv('OUT_IMG_PATH')}"
        self.out_tts_path = f"{out_path or os.getenv('OUT_TTS_PATH')}"
        self.file_metadata = {}
        self.file_metadata["pages"] = []
        self.file_page = {}
        self.file_page["elements"] = {}
        self.img_dpi = img_dpi
        self.page_index = []
        self.hashed_fname = self.create_fname_hash()
        # self.ouput_exists = self.create_dir() ## TODO: Remove after in-Memory
        self.s3_client = NoloBlobAPI()
        self.text_storage = {}  # In Memory Storage

        logger.info("Booklet Handler Created")

    # Utilities Functions
    def create_fname_hash(self):
        hashed_fname = hashlib.shake_128(self.fname.encode("utf-8")).hexdigest(4)
        # Create File Metadata Header
        self.file_metadata["doc_id"] = hashed_fname
        self.file_metadata["doc_name"] = self.fname[:-4].lower()
        self.file_metadata["doc_description"] = self.description
        self.file_metadata["modify_at"] = int(time.time())
        self.file_metadata["created_at"] = int(time.time())
        # hashed_fname = hashlib.shake_128(self.fname.encode("utf-8")).hexdigest(4)

        return hashed_fname

    def create_page_index_list(self, page_num, page_id):
        """
        Create a List of Tuples to associate a page_no with a page_id
        append it to the object
        """
        page_tuple = (page_num, page_id)
        self.page_index.append(page_tuple)
        return True

    def get_page_id_from_index(self, page_num):
        """
        return the page_id associated with the page_no
        """
        try:
            page_id = [item[1] for item in self.page_index if item[0] == page_num]
            return page_id[0]
        except Exception as e:
            logger.error(e)
            return None

    def get_page_data_dict(self, page_num) -> dict:
        """
        Return the page dict for the current page
        """
        try:
            page_data_dict = self.file_metadata["pages"][int(page_num) - 1]
            return page_data_dict
        except IndexError as e:
            logger.info(
                f"Error Creating a new Page {page_num} REASON: {e} ",
                extra={"error": "New Page"},
            )
            return None
        except Exception as e:
            logger.error(
                f"Failed to located a Page {page_num} REASON: {e}", extra={"error": e}
            )
            return None

    def get_file_metadata(self) -> dict:
        """
        Return File Metadata
        """

        return self.file_metadata

    def detect_text_language(self, text) -> tuple:
        """
        Detect Language in the extracted text
        """
        try:
            if text.strip() == "":
                # Text is empty"
                logger.warning(
                    "Language Detection received an empty string: Nothing to Detect"
                )
                return "", 0
            langs = detect_langs(text)
            for item in langs:
                # The first one returned is usually the one that has the highest probability
                return item.lang, int(item.prob * 100)
        except LangDetectException as e:
            logger.error(f"Language Detection fails! : {e}", extra={"error": e})
            return "err", 0

    # TTS
    def create_tts_from_text(self, tts_dict: dict):
        """
        Use AWS Polly to generate tts files in mp3 format
        """
        try:
            VoiceId = "Penelope" if tts_dict["gender"] == "female" else "Miguel"

            response = tts_client.synthesize_speech(
                VoiceId=VoiceId,
                OutputFormat="mp3",
                Text=tts_dict.get("tts_text"),
                Engine="standard",
            )

            audio_stream = io.BytesIO(response["AudioStream"].read())

            logger.info("TTS Creation success!")
            return audio_stream
        except Exception as e:
            logger.error(f"TTS Creation failed: REASON: {e}", extra={"error": e})
            raise e

    # SYNCH Functions
    # TODO: Eliminate this functio
    def delete_files_objects(self) -> bool:
        """
        Remove Local Files
        """
        try:
            # Erase Booklet
            os.remove(self.path)
            logger.info(f"File {self.path} deleted sucessful!")

            # Erase all Image files
            shutil.rmtree(f"./{self.out_img_path}/{self.hashed_fname}")
            logger.info(f"Images files for {self.fname} deleted sucessful!")

            # Erase all Text files
            shutil.rmtree(f"./{self.out_txt_path}/{self.hashed_fname}")
            logger.info(f"Text files for {self.fname} deleted sucessful!")

            # Erase all TTS files
            shutil.rmtree(f"./{self.out_tts_path}/{self.hashed_fname}")
            logger.info(f"TTS files for {self.fname} deleted sucessful!")

            return True
        except Exception as e:
            logger.error(f"Delete Operation failed. REASON: {e}", extra={"error": e})
            return False

    def create_dir(self) -> bool:
        """
        Create Local Dir (if required)
        """
        try:
            # Create Text Files Temporary Dir
            if not os.path.exists(f"./{self.out_txt_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_txt_path}/{self.hashed_fname}")
                logger.info(
                    f"Text path for Booklet {self.hashed_fname} created sucessfuly!"
                )

            # Create Image File Temporary Dir
            if not os.path.exists(f"./{self.out_img_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_img_path}/{self.hashed_fname}")
                logger.info(
                    f"Image path for Booklet {self.hashed_fname} created sucessfuly!"
                )

            # Create TTS Temporary dir
            if not os.path.exists(f"./{self.out_tts_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_tts_path}/{self.hashed_fname}")
                logger.info(
                    f"TTS path for Booklet {self.hashed_fname} created sucessfuly!"
                )

            return True
        except Exception as e:
            logger.error(e)
            return False

    # ASYNC Functions
    async def async_extract_text_from_file(self, file_data: bytes) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, self._extract_text_from_file_sync, file_data
                )
            logger.info("Booklet Text extracted sucessfuly!")
            return result
        except Exception as e:
            logger.error(f"Text extraction failed: REASON: {e}", extra={"error": e})
            return False

    async def async_create_image_from_file(self, file_data: bytes) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, self._create_image_from_file_sync, file_data
                )
            logger.info("Booklet Images extracted sucessfuly!")
            return result
        except Exception as e:
            logger.error(f"Image extraction failed: REASON: {e}", extra={"error": e})
            return False

    # ASYNC Helper Functions
    def _create_image_from_file_sync(self, file_data: bytes):
        """
        Image Extraction Function
        """
        images = convert_from_bytes(file_data, dpi=self.img_dpi)
        for page_num, image in enumerate(images, start=1):
            # Create a Unique pageID
            label_num = f"{page_num:02}"  # Format page number with leading 0
            img_fname = f"{self.hashed_fname}_page_{label_num}.png"

            # Capture Image Data
            img_bytes = io.BytesIO()
            image.save(img_bytes, "PNG")
            img_bytes.seek(0)

            # Upload to S3
            s3_img_file_name_key = f"img/{self.hashed_fname}/{img_fname}"
            self.s3_client.bucket.upload_fileobj(
                img_bytes, self.s3_client.bucket_name, s3_img_file_name_key
            )

            # Calculate Presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                s3_img_file_name_key, expires=os.getenv("URL_EXPIRATION_IN_SECS")
            )

            

            # cover page
            if page_num == 1:
                self.file_metadata["cover_img"] = presigned_url

            # Access Page MetaData
            page_data = self.get_page_data_dict(page_num)

            #AI Image Description. Create Logic to avoid sending
            # Text_only images or blank imnages
            # # Call Polly with a Different Gender (maybe female) from Text Reader

            img_ai_desc_lang = "es" if page_data["elements"]["lang"] != "en" else "en"
            logger.info("Sending Image to AI for Description")
            img_ai_desc = noloai.nolo_ai_description(presigned_url, img_ai_desc_lang)
            logger.info("Image Description from AI completed")

            # Create Synth Voice for img_tts_url and presigned
            if img_ai_desc is not None:
                logger.info(f"Creating IMG TTS File for Page {label_num}")
                # Send Only Text to Lang Detection and TTS
                lang, prob = self.detect_text_language(img_ai_desc)
                tts_dict = {
                    "tts_text": img_ai_desc.lower(),  # lower case for improve tts accuracy
                    "doc_id": self.hashed_fname,
                    "tts_file": f"{self.hashed_fname}_img_desc_page_{label_num}.mp3",
                    "language": lang,
                    "gender": "female",
                }

                tts_audio_stream = self.create_tts_from_text(tts_dict)
                s3_tts_file_name_key = (
                    f"tts/{self.hashed_fname}/{self.hashed_fname}_img_desc_page_{label_num}.mp3"
                )

                # Upload to s3
                self.s3_client.bucket.upload_fileobj(
                    tts_audio_stream, self.s3_client.bucket_name, s3_tts_file_name_key
                )

                # Calculate Presigned URL
                img_tts_presigned_url = self.s3_client.generate_presigned_url(
                    s3_tts_file_name_key, expires=os.getenv("URL_EXPIRATION_IN_SECS")
                )

            else:
                img_tts_presigned_url = None

            logger.info("PDF Image Description Proccess competed!")    
            


           # Prepare Data Dictionary to send it to DB
            logger.info("Prepare Booklet Data to DB competed! ")
            if page_data is None:
                """
                New Page
                """
                logger.info(f"Creating Page {page_num} imaging info")
                file_page = {}
                file_page["master_doc"] = self.hashed_fname
                file_page["page_num"] = page_num
                file_page["page_id"] = f"pg_{page_num}_{uuid4().hex}"
                file_page["file_name"] = img_fname
                file_page["img_url"] = presigned_url
                self.create_page_index_list(page_num, self.file_page["page_id"])
                file_page["elements"] = {
                    "image": img_fname,
                    "img_url": presigned_url,
                    "img_text": img_ai_desc,
                    "img_tts_url" : img_tts_presigned_url,
                    "create_img_tts": True,
                }
                self.file_metadata["pages"].append(file_page)
            else:
                """
                For Existing Pages, Add More MetaData to a Page
                """
                logger.info(f"Updating Page {page_num} image info")
                page_data["master_doc"] = self.hashed_fname
                page_data["file_name"] = img_fname
                page_data["elements"]["image"] = img_fname
                page_data["elements"]["img_url"] = presigned_url
                page_data["elements"]["img_text"] = img_ai_desc
                page_data["elements"]["img_tts_url"] = img_tts_presigned_url
                page_data["elements"]["create_img_tts"] = True

        #
        self.file_metadata["tts_ready"] = True        
        logger.info("Booklet Image Extraction succeded")
        return self.hashed_fname

    def _extract_text_from_file_sync(self, file_data: bytes) -> bool:
        booklet_file = fitz.open("pdf", file_data)
        # booklet_file = fitz.open(self.path)

        # Retrieve Text
        self.file_metadata["number_of_pages"] = len(booklet_file)
        for page_num, page in enumerate(booklet_file.pages(), start=1):
            text = page.get_text()
            text = cleaner.remove_unwanted_text(text)

            # Create TEXT Files from Content
            label_num = f"{page_num:02}"  # Format page number with leading 0

            # In Memory Version for ECS Support
            #
            key = f"{self.hashed_fname}_page_{label_num}"

            if key not in self.text_storage:
                self.text_storage[key] = ""
            self.text_storage[key] += text

            # Prepare text data for upload
            text_data = self.text_storage[key].encode()

            # Upload to S3
            s3_txt_file_name_key = (
                f"txt/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt"
            )
            self.s3_client.bucket.put_object(
                Bucket=self.s3_client.bucket_name,
                Key=s3_txt_file_name_key,
                Body=text_data,
            )

            # Create Pre-signed URL
            presigned_url = self.s3_client.generate_presigned_url(
                s3_txt_file_name_key, expires=os.getenv("URL_EXPIRATION_IN_SECS")
            )

            # Clear stored text
            del self.text_storage[key]

            # Create TTS File - Polly
            lang, prob = "", 0
            if text != "":
                logger.info(f"Creating TTS File for Page {label_num}")
                # Send Only Text to Lang Detection and TTS
                lang, prob = self.detect_text_language(text)
                tts_dict = {
                    "tts_text": text.lower(),  # lower case for improve tts accuracy
                    "doc_id": self.hashed_fname,
                    "tts_file": f"{self.hashed_fname}_page_{label_num}.mp3",
                    "language": lang,
                    "gender": "",
                }

                tts_audio_stream = self.create_tts_from_text(tts_dict)
                s3_tts_file_name_key = (
                    f"tts/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.mp3"
                )

                # Upload to s3
                self.s3_client.bucket.upload_fileobj(
                    tts_audio_stream, self.s3_client.bucket_name, s3_tts_file_name_key
                )

                # Calculate Presigned URL
                tts_presigned_url = self.s3_client.generate_presigned_url(
                    s3_tts_file_name_key, expires=os.getenv("URL_EXPIRATION_IN_SECS")
                )

            else:
                tts_presigned_url = None

            # Assign Page Metadata
            # Look for Existing the Page_ID in the Page Index, if not create one
            page_data = self.get_page_data_dict(page_num)
            if page_data is None:
                """
                For Any New Page Collect MetaData
                """
                logger.info(f"Creating Page {page_num} text info")
                file_page = {}
                file_page["master_doc"] = self.hashed_fname
                file_page["page_num"] = page_num
                file_page["page_id"] = f"pg_{label_num}_{uuid4().hex}"
                file_page["file_name"] = f"{self.hashed_fname}_page_{label_num}.txt"
                self.create_page_index_list(page_num, file_page["page_id"])
                file_page["elements"] = {
                    "text": text,
                    "lang": lang,
                    "lang_accuracy": prob,
                    "txt_file_url": presigned_url,
                    "tts_url": tts_presigned_url,
                    "create_txt_tts": False,
                }
                self.file_metadata["pages"].append(file_page)

            else:
                """
                For Existing Pages, just add the text element
                """
                logger.info(f"Updating Page {page_num} text info")
                page_data["master_doc"] = self.hashed_fname
                page_data["elements"]["text"] = text
                page_data["elements"]["lang"] = lang
                page_data["elements"]["lang_accuracy"] = prob
                page_data["elements"]["txt_file_url"] = presigned_url
                page_data["elements"]["tts_url"] = tts_presigned_url
                page_data["elements"]["create_txt_tts"] = False

        logger.info(f"Text Extraction sucedded booklet id {self.hashed_fname}")
        return self.hashed_fname
