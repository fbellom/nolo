import re
import logging


# Grok-like PATTERNS
URL_PATTERN = r"https?:\/\/(?:www\.)?[^\s]+"
WWW_PATTERN = r"www\.[^\s]+"
NEW_LINE_PATTERN = r"/\n"
NUMBER_AT_START = r"^.?\d+"
COPYRIGHT_MARK = r"(\N{COPYRIGHT SIGN}|\N{TRADE MARK SIGN}|\N{REGISTERED SIGN})"
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

# Logger
logger = logging.getLogger(__name__)


class NoloCleaner:
    """
    Utility to remove unwanted text from booklets
    """

    def __init__(self):
        self.clean_text = ""

    def remove_unwanted_text(self, raw_text: str) -> str:
        TEXT_SOURCE = raw_text

        try:
            # Step 1: Remove New Line \n
            cleaned_text = re.sub(NEW_LINE_PATTERN, "", TEXT_SOURCE)
            logger.info(f"New Line Removed")

            # cleaned_text = cleaned_text.strip()

            cleaned_text = re.sub(NUMBER_AT_START, "", cleaned_text)
            logger.info(f"NUMBER Line Removed")

            # Step 2: Remove URL References
            cleaned_text = re.sub(URL_PATTERN, "", cleaned_text)
            logger.info(f"URL Line Removed")

            # Step 2.1: Remove WWW References
            cleaned_text = re.sub(WWW_PATTERN, "", cleaned_text)
            logger.info(f"WWW Line Removed")

            # Step 2.2: Copy Right
            cleaned_text = cleaned_text.encode("utf-8")
            cleaned_text = re.sub(COPYRIGHT_MARK, "", cleaned_text.decode("utf-8"))
            logger.info(f"COPYRYGHT Line Removed")

            # Step 3: Remove any Email references
            cleaned_text = re.sub(EMAIL_PATTERN, "", cleaned_text)
            logger.info(f"Email Line Removed")

            # Final Stage put all in one line
            cleaned_text = cleaned_text.replace("\n", " ").strip()
            logger.info(f"Text Cleaning Complete")

            return cleaned_text
        except Exception as e:
            logger.error("Text Cleaner failed", extra={"erro": e})
            raise
