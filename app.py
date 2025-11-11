from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import mongo, jwt
from services.auth_service import auth_bp
from services.file_service import file_bp

app = Flask(__name__)
app.config.from_object(Config)

# ✅ Initialize extensions
mongo.init_app(app)
jwt.init_app(app)

# ✅ Enable CORS
CORS(app)

# ✅ Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(file_bp, url_prefix="/file")

@app.route("/")
def home():
    return jsonify({"message": "NimbusVault Backend is running 🚀"})

if __name__ == "__main__":
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
