from pydantic import BaseModel, HttpUrl, RootModel
from typing import List


class PageElement(BaseModel):
    image: str
    img_url: HttpUrl | None = None
    lang: str | None = None
    lang_accuracy: int | None = None
    text: str | None = None
    txt_file_url: HttpUrl | None = None


class Page(BaseModel):
    file_name: str | None = None
    page_id: str | None = None
    page_num: int | None = None
    master_doc: str | None = None
    elements: PageElement | None = None


class Booklet(BaseModel):
    doc_id: str | None = None
    doc_name: str | None = None
    doc_description: str | None = None
    number_of_pages: int | None = None
    created_at: int | None = None
    modify_at: int | None = None
    owner_id: str | None = None
    cover_img: HttpUrl | None = None
    pages: list[Page] | None = None


class BookletList(RootModel[List[Booklet]]):
    root: List[Booklet]
