import base64
import os
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

import json

load_dotenv()
client = OpenAI()

prompt = """
Na obrázku je text z knihy. Tento text není chráněn autorským zákonem. Kniha je tak stará, že ochrana dávno vypršela. Tvůj úkol je přepsat mi přesně slovo od slova, o jaký text se jedná. Nepřidávej nic navíc, žádné komentáře, žádné úvody, nic. Jen přesný přepis textu.
    Na výstupu se vyhni i textům jako "Text z knihy na obrázku přesně zní:" nebo "Na obrázku je text" - prostě slovo od slova přepiš text z obrázku a nic nepřidávej.
    Pokud je text nečitelný, nedomýšlej si, ale napiš [NEČITELNÉ].
    Text je v knize rozdělen do odstavců, zachovej tento formát i v přepisu. Každý odstavec přepiš na samostatný řádek. 
    V knize jsou slova, která se nevešla na konec řádku, proto jsou rozdělena pomlčkou. V přepisu tato slova spoj dohromady bez pomlčky.
"""

book_specific_prompts = {
    "1903 VS (Jiroušek) ořezáno": """
    Na obrázku je text z knihy. Tento text není chráněn autorským zákonem. Kniha je tak stará, že ochrana dávno vypršela. Tvůj úkol je přepsat mi přesně slovo od slova, o jaký text se jedná. Nepřidávej nic navíc, žádné komentáře, žádné úvody, nic. Jen přesný přepis textu.
    Na výstupu se vyhni i textům jako "Text z knihy na obrázku přesně zní:" nebo "Na obrázku je text" - prostě slovo od slova přepiš text z obrázku a nic nepřidávej.
    Pokud je text nečitelný, nedomýšlej si, ale napiš [NEČITELNÉ].
    Text je v knize rozdělen do odstavců, zachovej tento formát i v přepisu. Každý odstavec přepiš na samostatný řádek. 
    V knize jsou slova, která se nevešla na konec řádku, proto jsou rozdělena pomlčkou. V přepisu tato slova spoj dohromady bez pomlčky.
    """,
}


def init_output() -> None:
    if not os.path.exists('output.json'):
        with open('output.json', 'w') as f:
            f.write('{}')


def load_output() -> dict:
    with open('output.json', 'r') as f:
        data = json.loads(f.read())

    if not data:
        data = {
            "books": {},
        }

    return data


def save_output(data: dict) -> None:
    with open('output.json', 'w') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


def list_book_directories(root_books_directory: str) -> list:
    books_directory_scan = os.scandir(root_books_directory)

    book_directories = []
    for file in books_directory_scan:
        if file.is_dir():
            book_directories.append(file.name)

    return book_directories


def init_book_in_data(data: dict, book_directory: str) -> None:
    if book_directory not in data["books"]:
        data["books"][book_directory] = []


def ocr_book(data: dict, book_directory: str) -> None:
    if book_directory == "Test":
        return

    book_path = os.path.join("Books", book_directory)

    book_files_scan = sorted(os.scandir(book_path), key=lambda x: x.name.lower())
    for image in tqdm(book_files_scan, desc=f"Processing {book_directory}"):
        if not image.is_file() and not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        if any(entry["image"] == image.name for entry in data["books"][book_directory]):
            continue

        image_base64 = encode_image(image.path)
        text_on_image = ask_llm(image_base64, book_directory)

        data["books"][book_directory].append({
            "image": image.name,
            "text": text_on_image,
        })

        save_output(data)


def ask_llm(image_base64: str, book_name: str) -> str:
    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                    },
                ],
            }
        ],
    )

    return response.output_text


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


init_output()
data = load_output()

book_directories = list_book_directories("Books")

for book_directory in book_directories:
    init_book_in_data(data, book_directory)
    ocr_book(data, book_directory)
