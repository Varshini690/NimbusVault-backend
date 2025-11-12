import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import Config
from extensions import mongo  # ensure this is imported correctly

file_bp = Blueprint("file", __name__)

# ✅ AWS client setup
s3 = boto3.client(
    "s3",
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION,
)
BUCKET = Config.AWS_BUCKET_NAME


# ✅ Upload file (user-specific path)
@file_bp.route("/upload_url", methods=["POST"])
@jwt_required()
def generate_upload_url():
    data = request.get_json() or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400

    current_user = get_jwt_identity()  # get logged-in user

    try:
        # user folder: <username>/<filename>
        key_path = f"{current_user}/{filename}"

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION,
            endpoint_url=f"https://s3.{Config.AWS_REGION}.amazonaws.com"
        )

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": BUCKET, "Key": key_path},
            ExpiresIn=3600
        )

        # ✅ Store metadata in MongoDB (optional but recommended)
        mongo.db.files.update_one(
            {"owner": current_user, "filename": filename},
            {"$set": {"s3_key": key_path}},
            upsert=True
        )

        return jsonify({"upload_url": presigned_url}), 200

    except ClientError as e:
        print("❌ AWS Error:", e)
        return jsonify({"error": str(e)}), 500


# ✅ List files (only user's)
@file_bp.route("/list", methods=["GET"])
@jwt_required()
def list_files():
    current_user = get_jwt_identity()
    try:
        resp = s3.list_objects_v2(
            Bucket=BUCKET, Prefix=f"{current_user}/", MaxKeys=1000
        )
        contents = resp.get("Contents", [])
        files = [
            {"key": obj["Key"].replace(f"{current_user}/", ""), "size": obj["Size"]}
            for obj in contents
            if obj["Key"].startswith(f"{current_user}/")
        ]
        return jsonify({"files": files})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500


# ✅ Download (only user's)
@file_bp.route("/download_url", methods=["POST"])
@jwt_required()
def generate_download_url():
    data = request.get_json() or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400

    current_user = get_jwt_identity()
    key_path = f"{current_user}/{filename}"

    try:
        s3.head_object(Bucket=BUCKET, Key=key_path)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": key_path},
            ExpiresIn=600,
        )
        return jsonify({"download_url": url})
    except ClientError as e:
        return jsonify({"error": str(e)}), 404


# ✅ Delete (only user's)
@file_bp.route("/delete", methods=["POST"])
@jwt_required()
def delete_file():
    data = request.get_json() or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400

    current_user = get_jwt_identity()
    key_path = f"{current_user}/{filename}"

    try:
        s3.delete_object(Bucket=BUCKET, Key=key_path)
        mongo.db.files.delete_one({"owner": current_user, "filename": filename})
        return jsonify({"deleted": filename})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500
