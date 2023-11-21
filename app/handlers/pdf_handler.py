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
from handlers.s3_handler import NoloBlobAPI

class NoloPDFHandler:
    """
    Class to Manage Files Conversion
    """

    def __init__(self, file_name=None, path=None, out_path=None, img_dpi=72,description=None):
        self.fname = file_name or os.getenv("PDF_FILE")
        self.description = description or ""
        self.path = f"{path or os.getenv('PDF_PATH')}/{self.fname}"
        self.out_txt_path = f"{out_path or os.getenv('OUT_TXT_PATH')}"
        self.out_img_path = f"{out_path or os.getenv('OUT_IMG_PATH')}"
        self.file_metadata = {}
        self.file_metadata["pages"] = []
        self.file_page = {}
        self.file_page["elements"] = {}
        self.img_dpi = img_dpi
        self.page_index = []
        self.hashed_fname = self.create_fname_hash()
        self.ouput_exists = self.create_dir()
        self.s3_client = NoloBlobAPI()
        
        


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
                return item.lang, int(item.prob*100)
        except:
            return "err", 0    


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

            with open(f'./{self.out_img_path}/{self.hashed_fname}/{img_fname}', 'rb') as file_obj:
                #encoded_img = base64.b64encode(file_obj.read())
                # Upload to s3
                self.s3_client.bucket.upload_fileobj(file_obj,self.s3_client.bucket_name,f"img/{self.hashed_fname}/{img_fname}")

                s3_img_file_name = f"img/{self.hashed_fname}/{img_fname}"
                
                presigned_url = self.s3_client.generate_presigned_url(s3_img_file_name, expires=os.getenv("URL_EXPIRATION_IN_SECS"))
            # cover page
            if page_num == 1:
                self.file_metadata["cover_img"] = presigned_url 


            # Access Page MetaData
            page_data = self.get_page_data_dict(page_num)
            if page_data is None:
                """
                New Page
                """
                file_page = {}
                file_page["master_doc"] = self.hashed_fname
                file_page["page_num"] = page_num
                file_page["page_id"] = f"pg_{page_num}_{uuid4().hex}"
                file_page["file_name"] = img_fname
                file_page["img_url"] = presigned_url
                self.create_page_index_list(page_num, self.file_page["page_id"])
                file_page["elements"] = {"image" : img_fname, "img_url" : presigned_url}
                self.file_metadata["pages"].append(file_page)
            else:
                """
                For Existing Pages, Add More MetaData to a Page
                """
                page_data["master_doc"] = self.hashed_fname
                page_data["file_name"] = img_fname    
                page_data["elements"]["image"] = img_fname
                page_data["elements"]["img_url"] = presigned_url


            
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
                #page_num = f"0{page_num}"
                label_num = f"0{page_num}"
            else:
                label_num = f"{page_num}"    
            with open(
                f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt",
                "a",
            ) as file_obj:
                file_obj.writelines(text)
                lang, prob = self.detect_text_language(text)
                # Upload to s3
                self.s3_client.bucket.upload_file(
                    f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt",
                    self.s3_client.bucket_name,
                    f"txt/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt")

                s3_txt_file_name =  f"txt/{self.hashed_fname}/{self.hashed_fname}_page_{label_num}.txt" 
                presigned_url = self.s3_client.generate_presigned_url(s3_txt_file_name, expires=os.getenv("URL_EXPIRATION_IN_SECS"))



            # Assign Page Metadata    
            # Look for Existing the Page_ID in the Page Index, if not create one 
                page_data = self.get_page_data_dict(page_num)
                if page_data is None:
                    """
                    For Any New Page Collect MetaData
                    """
                    file_page = {}
                    file_page["master_doc"] = self.hashed_fname
                    file_page["page_num"] = page_num
                    file_page["page_id"] = f"pg_{label_num}_{uuid4().hex}"
                    file_page["file_name"] = f"{self.hashed_fname}_page_{label_num}.txt"
                    self.create_page_index_list(page_num, file_page["page_id"])
                    file_page["elements"]= {"text": text, 
                                            "lang" : lang, 
                                            "lang_accuracy" : prob,
                                            "txt_file_url" : presigned_url }
                    self.file_metadata["pages"].append(file_page)

                else:
                    """
                    For Existing Pages, just add the text element
                    """
                    page_data["master_doc"] = self.hashed_fname
                    page_data["elements"]["text"] = text
                    page_data["elements"]["lang"] = lang
                    page_data["elements"]["lang_accuracy"] = prob 
                    page_data["elements"]["txt_file_url"] = presigned_url
            
        return self.hashed_fname
    

        