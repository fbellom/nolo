import time
import os
import hashlib
from pathlib import Path
from pdf2image import convert_from_path
import fitz
import asyncio
from concurrent.futures import ThreadPoolExecutor
import base64
from uuid import uuid4
from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException
from handlers.s3_handler import NoloBlobAPI
from handlers.tts_handler import NoloTTS
from utils.text_cleaner import NoloCleaner
import logging
import shutil

# Create Logger
logger = logging.getLogger(__name__)

# Utils Import
cleaner = NoloCleaner()
polly = NoloTTS()
tts_client = polly.client

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
        self.ouput_exists = self.create_dir()
        self.s3_client = NoloBlobAPI()

        logger.info("PDF Handler Created")

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
            logger.info(f"Creating a new Page {page_num} ", extra={"error" : "New Page"})
            return None
        except Exception as e:
            logger.error(f"Failed to located a Page {page_num}", extra={"error" : e})
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
            if text.strip() == '':
                #Text is empty"
                logger.warning("Language Detection received an empty string: Nothing to Detect")
                return "",0
            langs = detect_langs(text)
            for item in langs:
                # The first one returned is usually the one that has the highest probability
                return item.lang, int(item.prob * 100)
        except LangDetectException as e:
            logger.error(f"Language Detection fails! : {e}", extra={"error" : e})
            return "err", 0

    # TTS
    def create_tts_from_text(self, tts_dict:dict) -> bool:
        """
        Use AWS Polly to generate tts files in mp3 format 
        """
        try:
            if tts_dict["gender"] == "female":
                VoiceId = "Penelope"
            else:
                VoiceId = "Miguel"

            filename = f"./{self.out_tts_path}/{self.hashed_fname}/{tts_dict.get('tts_file')}"

            response = tts_client.synthesize_speech(
            VoiceId=VoiceId,
            OutputFormat="mp3",
            Text=tts_dict.get("tts_text"),
            Engine="standard",
            )

            with open(filename, "wb") as tts:
                tts.write(response["AudioStream"].read())    

            
            return True
        except Exception as e:
            logger.error(f"TTS Creation failed: REASON: {e}", extra={"error" : e})
            return False        

    # SYNCH Functions
    def delete_files_objects(self) -> bool:

        try:
            # Erase pdf
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
            logger.error(f"Delete Operation failed. REASON: {e}", extra={"error" : e})
            return False    

    def create_dir(self) -> bool:
        try:
            #Create Text Files Temporary Dir
            if not os.path.exists(f"./{self.out_txt_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_txt_path}/{self.hashed_fname}")
                logger.info(f"PDF Text path for booklet {self.hashed_fname} created sucessfuly!")

            #Create Image File Temporary Dir
            if not os.path.exists(f"./{self.out_img_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_img_path}/{self.hashed_fname}")
                logger.info(f"PDF Image path for booklet {self.hashed_fname} created sucessfuly!")
            
            #Create TTS Temporary dir
            if not os.path.exists(f"./{self.out_tts_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_tts_path}/{self.hashed_fname}")
                logger.info(f"PDF TTS path for booklet {self.hashed_fname} created sucessfuly!")    

            return True
        except Exception as e:
            logger.error(e)
            return False

    # ASYNC Functions
    async def async_extract_text_from_file(self) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, self._extract_text_from_file_sync
                )
            logger.info("PDF Text extracted sucessfuly!")    
            return result
        except Exception as e:
            logger.error(f"Text extraction failed: REASON: {e}", extra={"error" : e})
            return False


    async def async_create_image_from_file(self) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, self._create_image_from_file_sync
                )
            logger.info("PDF Images extracted sucessfuly!")      
            return result
        except Exception as e:
            logger.error(f"Image extraction failed: REASON: {e}", extra={"error" : e})
            return False



    # ASYNC Helper Functions
    def _create_image_from_file_sync(self):
        save_path = Path(f"./{self.out_img_path}/{self.hashed_fname}")
        images = convert_from_path(self.path, dpi=self.img_dpi)
        for page_num, image in enumerate(images, start=1):
            # Create a Unique pageID
            if page_num < 10:
                # page_num = f"0{page_num}"
                label_num = f"0{page_num}"
            else:
                label_num = f"{page_num}"

            img_fname = f"{self.hashed_fname}_page_{label_num}.png"
            image.save(save_path / img_fname, "PNG")

            with open(
                f"./{self.out_img_path}/{self.hashed_fname}/{img_fname}", "rb"
            ) as file_obj:
                # encoded_img = base64.b64encode(file_obj.read())
                # Upload to s3
                self.s3_client.bucket.upload_fileobj(
                    file_obj,
                    self.s3_client.bucket_name,
                    f"img/{self.hashed_fname}/{img_fname}",
                )

                s3_img_file_name = f"img/{self.hashed_fname}/{img_fname}"

                presigned_url = self.s3_client.generate_presigned_url(
                    s3_img_file_name, expires=os.getenv("URL_EXPIRATION_IN_SECS")
                )
            # cover page
            if page_num == 1:
                self.file_metadata["cover_img"] = presigned_url

            # Access Page MetaData
            page_data = self.get_page_data_dict(page_num)
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
                file_page["elements"] = {"image": img_fname, "img_url": presigned_url}
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

        # TODO: Return File Path
        logger.info("Image Extraction succeded")
        return self.hashed_fname

    def _extract_text_from_file_sync(self) -> bool:

        pdf_file = fitz.open(self.path)


        # Retrieve Text
        self.file_metadata["number_of_pages"] = len(pdf_file)
        for page_num, page in enumerate(pdf_file.pages(), start=1):
            text = page.get_text()
            text = cleaner.remove_unwanted_text(text)


            # Create TEXT Files from Content
            if page_num < 10:
                # page_num = f"0{page_num}"
                label_num = f"0{page_num}"
            else:
                label_num = f"{page_num}"
            with open(
                f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt",
                "a",
            ) as file_obj:
                file_obj.writelines(text)
                lang, prob = "",0
               

                # Upload to s3
                self.s3_client.bucket.upload_file(
                    f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt",
                    self.s3_client.bucket_name,
                    f"txt/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt",
                )

                s3_txt_file_name = (
                    f"txt/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt"
                )
                presigned_url = self.s3_client.generate_presigned_url(
                    s3_txt_file_name, expires=os.getenv("URL_EXPIRATION_IN_SECS")
                )

                # Create TTS File
                if text != '':
                    logger.info(f"Creating TTS File for Page {label_num}")
                    # Send Only Text to Lang Detection and TTS
                    lang, prob = self.detect_text_language(text)
                    tts_dict = {
                        "tts_text" : text,
                        "doc_id" : self.hashed_fname,
                        "tts_file" : f"{self.hashed_fname}_page_{label_num}.mp3",
                        "language" : lang,
                        "gender" : ""
                    }

                    tts_response = self.create_tts_from_text(tts_dict)
                    if tts_response:
                        #Upload to s3
                        self.s3_client.bucket.upload_file(
                            f"./{self.out_tts_path}/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.mp3",
                            self.s3_client.bucket_name,
                            f"tts/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.mp3",
                        )

                        # Capture s3 Object TTS Filename
                        s3_tts_file_name = (
                            f"tts/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.mp3"
                        )

                        # Create the presigned URL
                        tts_presigned_url = self.s3_client.generate_presigned_url(
                            s3_tts_file_name, expires=os.getenv("URL_EXPIRATION_IN_SECS")
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
                        "tts_url" : tts_presigned_url
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

        logger.info("Text Extraction sucedded")
        return self.hashed_fname



