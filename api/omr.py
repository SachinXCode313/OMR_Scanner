import base64
import os
from flask import Flask, request, jsonify
from pathlib import Path

from src.service.omr_service import process_image_bytes, result_to_json

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "inputs" / "template.json"

@app.route("/omr/scan", methods=["POST"])
def check_omr():
    data = request.get_json(silent=True)

    if not data or "image_base64" not in data:
        return jsonify({"error": "image_base64 required"}), 400

    image_b64 = data["image_base64"]

    # 🔥 Strip data URI if Zoho sends it
    if "," in image_b64:
        image_b64 = image_b64.split(",")[1]

    try:
        image_bytes = base64.b64decode(image_b64)

        result = process_image_bytes(
            image_bytes=image_bytes,
            filename="zoho_upload.jpg",
            template_path=TEMPLATE_PATH,
        )

        return jsonify(result_to_json(result))

    except Exception as e:
        return jsonify({"error": "OMR processing failed"}), 500


@app.route("/omr/ping", methods=["GET"])
def health_check():
    return jsonify({
        "status": "awake",
        "service": "omr-scanner"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

