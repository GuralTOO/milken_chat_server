import weaviate
import dotenv
import os
import pypdf
from pdf2image import convert_from_path
import pytesseract
import json
import io
import requests
import my_mongodb

dotenv.load_dotenv()
client = weaviate.Client(
    url="http://206.189.199.72:8080/",  # Replace with your endpoint
    additional_headers={
        "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
    }
)

classes = client.schema.get().get("classes")


# get all class names
def get_class_names():
    class_names = [c["class"] for c in classes]
    return class_names

# get class with a given name


def get_class(class_name):
    class_ = next(filter(lambda c: c["class"] == class_name, classes), None)
    return class_

# add class to database


def add_class(class_name, description="", variables=[]):
    try:
        properties = []
        for var in variables:
            properties.append(
                {"dataType": ["text"], "name": var, "description": var})
        class_obj = {
            "class": class_name,
            "description": description,
            "properties": properties,
            "vectorizer": "text2vec-openai"
        }
        client.schema.create_class(class_obj)
    except:
        print("Class already exists")


# delete class from database


def delete_class(class_name):
    try:
        client.schema.delete_class(class_name=class_name)
    except:
        print("Class does not exist")

# add item to database


def check_if_item_exists(class_name, item):
    try:
        results = client.query.get(class_name=class_name, properties=["url", "page_text"]).with_where(
            {"path": "page_text", "operator": "Equal", "valueString": item["page_text"]}).with_limit(1).do()
        if results["data"]["Get"][class_name]:
            return True
    except:
        return False


def add_item(class_name, item):
    if not check_if_item_exists(class_name=class_name, item=item):
        client.data_object.create(class_name=class_name, data_object=item)
    else:
        print("Item already exists")


def load_page(class_name, text, url):
    try:
        # split text into into chunks of 1000 characters
        text_chunks = [text[i:i + 1000] for i in range(0, len(text), 1000)]
        for chunk in text_chunks:
            add_item(class_name=class_name, item={
                     "page_text": chunk, "url": url})
    except:
        print("Error loading page")


def load_pdf(class_name, url):
    try:
        # load file from a given url
        response = requests.get(url)
        response.raise_for_status()
        pdf_file = io.BytesIO(response.content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        pages_text = []
        pageCounter = 0

        for page in range(num_pages):
            images = convert_from_path(
                url, first_page=page + 1, last_page=page + 1)
            # if there are images in the page, use OCR to extract text
            if images:
                page_image = images[0]
                page_text = pytesseract.image_to_string(page_image)
                pages_text.append(page_text)
            # if there are no images in the page, use PyPDF2 to extract text
            else:
                page_obj = pdf_reader.getPage(page)
                page_text = page_obj.extractText()
                pages_text.append(page_text)

            # split text into into chunks of 1000 characters
            text_chunks = [page_text[i:i + 1000]
                           for i in range(0, len(page_text), 1000)]
            for chunk in text_chunks:
                add_item(class_name=class_name, item={
                         "page_text": chunk, "url": url})

            pageCounter += 1

        pdf_file.close()

        return "Success"
    except:
        print("Error loading pdf")


def add_items(class_name, items):
    with client.batch as batch:
        batch.batch_size = 100
        for item in items:
            batch.add_data_object(class_name=class_name, data_object=item)


# search for items in a class using nearest neighbor search
def search_items(class_name, variables=[""], text_query="", k=10):
    results = client.query.get(class_name=class_name, properties=variables).with_near_text(
        {"concepts": text_query}).with_limit(k).do()
    return results["data"]["Get"][class_name]

# return all items in a class


def get_all_items(class_name, variables=[""]):
    results = client.query.get(
        class_name=class_name, properties=variables).do()
    return results["data"]["Get"][class_name]


def load_pages():
    all_pages = list(my_mongodb.get_everything("milkenpages"))
    print("starting to load " + str(len(all_pages)) + " pages" + "\n")
    for page in all_pages:
        load_page(class_name="Milken_Institute_data",
                  text=page["text"], url=page["url"])
    print("loaded " + str(len(all_pages)) + " pages")


def load_pdfs():
    all_pdfs = list(my_mongodb.get_everything("milkendocuments"))
    print("starting to load " + str(len(all_pdfs)) + " pdfs" + "\n")

    for pdf in all_pdfs:
        # check if pdf ends with .pdf
        if pdf["url"].endswith(".pdf"):
            counter = counter + 1
            load_pdf(class_name="Milken_Institute_data", url=pdf["url"])

    print("loaded " + str(counter) + " pdfs")


# load_pages()

all_docs = list(my_mongodb.get_everything("milkendocuments"))
counter = 0
for page in all_docs:
    counter = counter + 1
    print(page["url"])
    print("\n")
    if counter == 25:
        break

# print(get_class_names())
# print(get_class("SampleParagraph")["properties"])
# add_items(class_name="SampleParagraph", items=[{"page_text": "Hello World", }])
# print(get_all_items("SampleParagraph", "page_text"))
# print(search_items(class_name="SampleParagraph", variables=[
#       "page_text"], text_query="Kamisha Mason", k=1))
# load_pdf("SampleParagraph",
#          "https://www.economicclub.org/sites/default/files/Kamisha%20Mason_Final.pdf")

# delete_class("Econ_club_data")
add_class("Milken_Institute_data", "Web scraped or pdf loaded documents from the Milken Institute website",
          ["url", "page_text"])

# add_item("Econ_club_data", {
#          "url": "https://www.economicclub.org/sites/default/files/Kamisha%20Mason_Final.pdf", "page_text": "Hello World"})
# load_pdf("Econ_club_data",
#          "https://www.economicclub.org/sites/default/files/Kamisha%20Mason_Final.pdf")
# print(get_all_items("Econ_club_data", ["url", "page_text"]))

# export all functions

load_pages()
load_pdfs()

# print(my_mongodb.get_count("pages"))
# # print the length of the array returned from get_everything
# all_pages = list(my_mongodb.get_everything("pages"))
# counter = 0
# for page in all_pages:
#     counter = counter + 1
#     print(page["url"])
#     print(page["text"])
#     print("\n")
#     if counter == 3:
#         break
