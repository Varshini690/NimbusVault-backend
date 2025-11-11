import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    
    # JWT Config
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")

    # 👇 Add this line to make tokens never expire
    JWT_ACCESS_TOKEN_EXPIRES = False
