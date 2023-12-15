import datetime
from pydantic import BaseModel, HttpUrl, RootModel, Field, constr
from typing import List, Optional


class PageElement(BaseModel):
    image: Optional[str] = None
    img_url: Optional[HttpUrl] = None
    lang: Optional[str] = None
    lang_accuracy: Optional[int] = None
    text: Optional[str] = None
    txt_file_url: Optional[HttpUrl] = None
    tts_url: Optional[HttpUrl] = None
    img_text: Optional[constr(max_length=400)] = None
    img_tts_url: Optional[HttpUrl] = None
    create_img_tts: bool = Field(
        default=True, description="Indicates if the page is ready for text-to-speech"
    )
    create_txt_tts: bool = Field(
        default=True, description="Indicates if the page is ready for text-to-speech"
    )


class Page(BaseModel):
    file_name: Optional[str] = None
    page_id: Optional[str] = None
    page_num: Optional[int] = None
    master_doc: Optional[str] = None
    elements: PageElement | None = None


class Booklet(BaseModel):
    doc_id: Optional[str] = None
    doc_name: Optional[str] = None
    doc_title: Optional[str] = None
    doc_description: Optional[constr(max_length=400)] = None
    number_of_pages: Optional[int] = None
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.now().timestamp())
    )
    modify_at: int = Field(
        default_factory=lambda: int(datetime.datetime.now().timestamp())
    )
    owner_id: Optional[str] = None
    cover_img: Optional[HttpUrl] = None
    is_published: bool = Field(
        default=True, description="Indicates if the booklet is published"
    )
    tts_ready: bool = Field(
        default=True, description="Indicates if the booklet is ready for text-to-speech"
    )
    pages: Optional[list[Page]] = None


class BookletList(RootModel[List[Booklet]]):
    root: List[Booklet]


# Partial Edits Models
class PageElementEdit(BaseModel):
    text: Optional[str] = None
    img_text: Optional[constr(max_length=400)] = None


class PageEdit(BaseModel):
    page_num: Optional[int] = None
    elements: PageElementEdit | None = None


class BookletEdit(BaseModel):
    doc_title: Optional[str] = None
    doc_description: Optional[str] = None
    pages: list[PageEdit] | None = None


class BookletTask(BaseModel):
    message: Optional[str] = None
    task_id: Optional[str] = None

class TaskStatus(BaseModel):
    task_id: Optional[str] = None
    status: Optional[str] = None

