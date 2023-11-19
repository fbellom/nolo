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


class NoloPDFHandler:
    """
    Class to Manage Files Conversion
    """

    def __init__(self, file_name=None, path=None, out_path=None):
        self.fname = file_name or os.getenv("PDF_FILE")
        self.path = f"{path or os.getenv('PDF_PATH')}/{self.fname}"
        self.out_txt_path = f"{out_path or os.getenv('OUT_TXT_PATH')}"
        self.out_img_path = f"{out_path or os.getenv('OUT_IMG_PATH')}"
        self.file_metadata = {}
        self.file_metadata["pages"] = []
        self.file_page = {}
        self.file_page["elements"] = {}
        self.page_index = []
        self.hashed_fname = self.create_fname_hash()
        self.ouput_exists = self.create_dir()
        


# Utilities Functions
    def create_fname_hash(self):
        hashed_fname = hashlib.shake_128(self.fname.encode("utf-8")).hexdigest(4)
        # Create File Metadata Header
        self.file_metadata["id"] = hashed_fname
        self.file_metadata["name"] = self.fname
        self.file_metadata["modify_at"] = int(time.time())
        self.file_metadata["created_at"] = int(time.time())
        # hashed_fname = hashlib.shake_128(self.fname.encode("utf-8")).hexdigest(4)

        return hashed_fname
    
    def create_page_index_list(self,page_num,page_id):
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
            page_id = [item[1] for item in self.page_index if item[0] == page_num ]
            return page_id[0]
        except Exception as e:
            print(e)
            return None

    def get_page_data_dict(self,page_num) -> dict:
        """
        Return the page dict for the current page
        """
        try:
            page_data_dict = self.file_metadata["pages"][int(page_num) - 1]
            return page_data_dict
        except IndexError:
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
            langs = detect_langs(text)
            for item in langs:
                # The first one returned is usually the one that has the highest probability
                return item.lang, item.prob
        except:
            return "err", 0.0    


# SYNCH Functions
    def create_dir(self) -> bool:
        try:
            if not os.path.exists(f"./{self.out_txt_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_txt_path}/{self.hashed_fname}")

            if not os.path.exists(f"./{self.out_img_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_img_path}/{self.hashed_fname}")

            return True
        except Exception as e:
            print(e)
            return False

    def create_image_from_file(self) -> bool:
        try:
            save_path = Path(f"./{self.out_img_path}/{self.hashed_fname}")
            images = convert_from_path(self.path)
            for page_num, image in enumerate(images, start=1):
                if page_num < 10:
                    page_num = f"0{page_num}"

                img_fname = f"{self.hashed_fname}_page_{page_num}.png"
                image.save(save_path / img_fname, "PNG")

            # TODO: Return File Path
            
            return self.hashed_fname
        except Exception as e:
            return False
    
    def extract_text_from_file(self) -> bool:
        try:
            pdf_file = fitz.open(self.path)

            # Retrieve Text
            for page_num, page in enumerate(pdf_file.pages(), start=1):
                text = page.get_text()
                if page_num < 10:
                    page_num = f"0{page_num}"

                with open(
                    f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{page_num}.txt",
                    "a",
                ) as txt:
                    txt.writelines(text)
                    # Detect Language
                    lang, prob = self.detect_text_language(text)
                    self.file_metadata["lang"] = lang
                    self.file_metadata["lang_prediction_accuracy"] = prob
            return self.hashed_fname
        except Exception as e:
            return False
        
# ASYNC Functions
    async def async_create_dir(self) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, self._create_dir_sync)
            return True
        except Exception as e:
            print(e)
            return False 

    async def async_create_image_from_file(self) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, self._create_image_from_file_sync)
            return result
        except Exception as e:
            print(e)
            return False


    async def async_extract_text_from_file(self) -> bool:
        loop = asyncio.get_running_loop()
        try:
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, self._extract_text_from_file_sync)
            return result
        except Exception as e:
            print(e)
            return False                    


    
    def _create_dir_sync(self) -> bool:
        try:
            if not os.path.exists(f"./{self.out_txt_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_txt_path}/{self.hashed_fname}")

            if not os.path.exists(f"./{self.out_img_path}/{self.hashed_fname}"):
                os.makedirs(f"./{self.out_img_path}/{self.hashed_fname}")

            return True
        except Exception as e:
            print(e)
            return False
        

    def _create_image_from_file_sync(self):
        save_path = Path(f"./{self.out_img_path}/{self.hashed_fname}")
        images = convert_from_path(self.path)
        for page_num, image in enumerate(images, start=1):
            # Create a Unique pageID
            if page_num < 10:
                page_num = f"0{page_num}"
            
            img_fname = f"{self.hashed_fname}_page_{page_num}.png"
            image.save(save_path / img_fname, "PNG")

            with open(f'./{self.out_img_path}/{self.hashed_fname}/{img_fname}', 'rb') as file_obj:
                encoded_img = base64.b64encode(file_obj.read())

            # Access Page MetaData
            page_data = self.get_page_data_dict(page_num)
            if page_data is None:
                """
                New Page
                """
                file_page = {}
                file_page["page_num"] = page_num
                file_page["page_id"] = f"pg_{page_num}_{uuid4().hex}"
                self.create_page_index_list(page_num, self.file_page["page_id"])
                file_page["full_image"] = f"data:image/jpeg;base64,{encoded_img}"
                file_page["elements"] = {"image" : f"data:image/jpeg;base64,{encoded_img}"}
                self.file_metadata["pages"].append(file_page)
            else:
                """
                Add More MetaData to a Page
                """    
                page_data["full_image"] = f"data:image/jpeg;base64,{encoded_img}"
                page_data["elements"]["image"] = f"data:image/jpeg;base64,{encoded_img}"


            
        # TODO: Return File Path
        return self.hashed_fname
    
    def _extract_text_from_file_sync(self) -> bool:
        pdf_file = fitz.open(self.path)
        # Retrieve Text
        self.file_metadata["number_of_pages"] = len(pdf_file)
        for page_num, page in enumerate(pdf_file.pages(), start=1):
            text = page.get_text()

            # Create TEXT Files from Content
            if page_num < 10:
                page_num = f"0{page_num}"
            with open(
                f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{page_num}.txt",
                "a",
            ) as txt:
                txt.writelines(text)
                lang, prob = self.detect_text_language(text)
                # self.file_metadata["lang"] = lang
                # self.file_metadata["lang_prediction_accuracy"] = prob

            # Assign Page Metadata    
            # Look for Existing the Page_ID in the Page Index, if not create one 
                page_data = self.get_page_data_dict(page_num)
                if page_data is None:
                    """
                    For Any New Page Collect MetaData
                    """
                    file_page = {}
                    file_page["page_num"] = page_num
                    file_page["page_id"] = f"pg_{page_num}_{uuid4().hex}"
                    self.create_page_index_list(page_num, file_page["page_id"])
                    file_page["elements"]= {"text": text, "lang" : lang, "lang_accuracy" : prob}
                    self.file_metadata["pages"].append(file_page)

                else:
                    """
                    For Existing Pages, just add the text element
                    """
                    page_data["elements"]["text"] = text
            
        return self.hashed_fname
    

        