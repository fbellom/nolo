from openai import OpenAI
from settings.nolo_config import NoloCFG
import logging


# Create Logger
logger = logging.getLogger(__name__)


# UTILS Class
# Utils Import
config = NoloCFG()


BASE_PROMPT_ES = f"""Puedes describir esta imagen para un niño con discapacidad visual de 5 a 10 años de edad, 
como una maestra de educacion especial? Manten el lenguaje sencillo y en español y 
hazlo en menos {config.openai_min_lines} lineas y {config.openai_max_char} caracteres"""

BASE_PROMT_EN = f"""Can you describe this image for a visually impaired child aged 5 to 10, 
as a special education teacher? Keep the language simple and in English, 
and do it in less than {config.openai_min_lines} lines and {config.openai_max_char} characters.
"""

GPT_MODEL = config.openai_model


class NoloAIHelper:
    """
    Class to Use AI for Image Description
    """

    def __init__(self):
        """
        NoloAIHelper Constructor
        """
        self.client = OpenAI(
            api_key=config.openai_api_key, organization=config.openai_org_id
        )

        self.prompts = {
            "es": {"user": BASE_PROMPT_ES.strip()},
            "en": {"user": BASE_PROMT_EN.strip()},
        }

        logger.info("New Instance of AI Helper has been created")

    def nolo_ai_description(self, img_url: str, lang: str = "es") -> str | None:
        try:
            # Check if languages exist in the dictionary
            if lang not in list(self.prompts.keys()):
                logger.warning(
                    f"AI Services stopped because {lang} is not defined as valid!"
                )
                return None
            # Clear the response string
            img_ai_description = ""
            # Create a Description from the URL and the PROMPT condition
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.prompts[lang]["user"]},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
                max_tokens=config.openai_max_tkn,
            )

            img_ai_description = response.choices[0].message.content

            return img_ai_description

        except Exception as e:
            logger.error(f"A problem with the ai services occurs. REASON: {e}")
            raise
