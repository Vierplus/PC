import pymongo

mongo_uri = "mongodb://vierplus:4plus@100.108.16.72:27017/VM_DB"

try:
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_database()
    print("Connected successfully!")
except pymongo.errors.OperationFailure as e:
    print(f"Authentication failed: {e}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")