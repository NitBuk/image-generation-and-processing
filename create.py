# create.py

##############################################################################
#                                   Imports                                  #
##############################################################################
import json
from pathlib import Path
from keys import *
import openai

def create_json(prompt):
    DATA_DIR = Path.cwd() / "responses"
    DATA_DIR.mkdir(exist_ok=True)
    openai.api_key = OPENAI_API_KEY
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="b64_json",
    )
    file_name = DATA_DIR / f"{prompt[:5]}-{response['created']}.json"
    with open(file_name, mode="w", encoding="utf-8") as file:
        json.dump(response, file)
    return file_name
