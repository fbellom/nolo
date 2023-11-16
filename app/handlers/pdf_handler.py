import os
import hashlib
from pathlib import Path
from pdf2image import convert_from_path
import fitz


class NoloPDFHandler:
    """
    Class to Manage Files Conversion
    """

    def __init__(self, file_name=None, path=None, out_path=None):
        self.fname = file_name or os.getenv("PDF_FILE")
        self.path = f"{path or os.getenv('PDF_PATH')}/{self.fname}"
        self.out_txt_path = f"{out_path or os.getenv('OUT_TXT_PATH')}"
        self.out_img_path = f"{out_path or os.getenv('OUT_IMG_PATH')}"
        self.hashed_fname = self.create_fname_hash()
        self.ouput_exists = self.create_dir()

    def create_fname_hash(self):
        hashed_fname = hashlib.shake_128(self.fname.encode("utf-8")).hexdigest(4)
        return hashed_fname

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
            for page_id, image in enumerate(images, start=1):
                if page_id < 10:
                    page_id = f"0{page_id}"

                img_fname = f"{self.hashed_fname}_page_{page_id}.png"
                image.save(save_path / img_fname, "PNG")

            # TODO: Return File Path
            return self.hashed_fname
        except Exception as e:
            return False

    def extract_text_from_file(self) -> bool:
        try:
            pdf_file = fitz.open(self.path)

            # Retrieve Text
            for page_id, page in enumerate(pdf_file.pages(), start=1):
                text = page.get_text()
                if page_id < 10:
                    page_id = f"0{page_id}"

                with open(
                    f"./{self.out_txt_path}/{self.hashed_fname}/{self.hashed_fname}_page_{page_id}.txt",
                    "a",
                ) as txt:
                    txt.writelines(text)
            return self.hashed_fname
        except Exception as e:
            return False
