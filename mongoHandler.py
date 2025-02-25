import os
from pymongo import MongoClient
from dotenv import load_dotenv

def get_db():
   """
   Creates and returns a handle to the MongoDB database.
   Uses env variables for configuration.
   :return:
   """

   load_dotenv()

   mongo_uri = os.environ.get('MONGO_URI')
   mongo_db_name: str = os.environ.get('MONGO_DB_NAME')
   print(mongo_db_name)
   print(mongo_uri)
   client = MongoClient(mongo_uri)
   db = client[mongo_db_name]
   return db

