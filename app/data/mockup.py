import json
import random
import string


SINGLE_DOCUMENT={
  "id": "326d3540",
  "name": "Espacio Imaginario",
  "lang": "es_PR",
  "category": "",
  "tags": [],
  "version": "",
  "last_modify": "",
  "created_at": "",
  "owner_id": "326d3540",
  "pages" : [
      {
      "page": 1,
      "id": "326d3540",
      "full_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA",
      "elements" : {
          "text" : "",
          "tts" : "",
          "image_descriptor" : "",
          "image" : "",
          "image_tts" : "",
          "interactive" : 0
        }
      } 
  ]
}




# Function
def random_string(length=8) -> str:
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def randomize_document_struct(document,num_copies=3):
    randomized_copies=[]
    for _ in range(num_copies):
        copy_doc = document.copy()
        copy_doc['id'] = copy_doc['owner_id'] = random_string(8)
        
        for page in copy_doc['pages']:
            page['id'] = copy_doc['id']
            page['page'] = random.randint(1, 100)  # Random page number

            for key in page['elements'].keys():
                if isinstance(page['elements'][key], int):
                    page['elements'][key] = random.randint(0, 1)  # Random binary value
                else:
                    # Ensure unique random strings for each field
                    page['elements'][key] = random_string(10)  # Random string for text fields

        randomized_copies.append(copy_doc)

    return randomized_copies    


class DUMMYData:
    def __init__(self,num_copies=None) -> None:
        self.version='1.0.0'
        self.num_copies=5 or num_copies

    def create_multiple_docs(self):
        randomized_documents = randomize_document_struct(SINGLE_DOCUMENT,self.num_copies)  
        return randomized_documents 
    
    def create_single_doc(self):
        return SINGLE_DOCUMENT

    