import json


with open("output.json", "r") as text_file:
    data = json.loads(text_file.read())

for book in data["books"]:
    formated_book = ""

    for page in sorted(data["books"][book], key=lambda x: x["image"]):
        formated_book += page["image"] + "\n========================\n"
        formated_book += page["text"] + "\n\n\n"

    with open(f"Books Text/{book}.txt", "w") as text_file:
        text_file.write(formated_book)
