# connect to mongodb
from pymongo import MongoClient
import dotenv
import os
dotenv.load_dotenv()

print(os.environ["MONGODB_URL"])
client = MongoClient(os.environ["MONGODB_URL"])

db_name = "test"
db = client.get_database(db_name)


def get_collection_names():
    return db.list_collection_names()


def get_count(collection_name, filter={}):
    return db.get_collection(collection_name).count_documents(filter=filter)


def get_everything(collection_name, filter={}):
    return db.get_collection(collection_name).find(filter=filter)


print(get_collection_names())

# close connection to mongodb

# iterate over documents in collection
# counter = 0
# for doc in db.get_collection(collection_name).find(filter=filter):
#     print(doc["url"])
#     counter = counter + 1
#     if counter == 10:
#         break

# counter = 0
# for doc in db.get_collection("documents").find(filter=filter):
#     print(doc["url"])
#     counter = counter + 1
#     if counter == 10:
#         break
