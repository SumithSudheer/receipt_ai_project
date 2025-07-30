import json
import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DISCOVERED_FILE = "tests/discovered_data.json"

def append_discovered_data(file_name, data):
    discovered = []
    if os.path.exists(DISCOVERED_FILE):
        with open(DISCOVERED_FILE, "r") as f:
            try:
                discovered = json.load(f)
            except json.JSONDecodeError:
                discovered = []
    discovered.append({
        "file": file_name,
        "extracted": data
    })
    with open(DISCOVERED_FILE, "w") as f:
        json.dump(discovered, f, indent=2)

def load_index_files():
    with open("index.txt", "r") as f:
        return [line.strip() for line in f if line.strip().endswith(".pdf")]

def load_expected_data():
    try:
        with open("tests/test_data.json", "r") as f:
            return {item["file"]: item["expected"] for item in json.load(f)}
    except FileNotFoundError:
        return {}

def test_receipt_api_full():
    files = load_index_files()
    expected_data = load_expected_data()

    for file_path in files:
        file_name = os.path.basename(file_path)

        # Step 1: Upload
        with open(file_path, "rb") as f:
            upload_resp = client.post("/upload", files={"file": f})
        assert upload_resp.status_code == 200
        file_id = upload_resp.json()["file_id"]

        # Step 2: Validate
        validate_resp = client.post(f"/validate/{file_id}")
        assert validate_resp.status_code == 200
        assert validate_resp.json()["is_valid"] is True

        # Step 3: Process
        process_resp = client.post(f"/process/{file_id}")
        assert process_resp.status_code == 200
        result = process_resp.json()

        # Check against expected if available
        if file_name in expected_data:
            expected = expected_data[file_name]
            assert expected["merchant_name"].lower() in result["merchant_name"].lower(), \
                f"Merchant mismatch in {file_name}"
            assert abs(result["total_amount"] - expected["total_amount"]) < 0.01, \
                f"Amount mismatch in {file_name}"
            assert result["purchased_at"] == expected["purchased_at"], \
                f"Date mismatch in {file_name}"
            print(f"✅ FULL CHECK PASSED: {file_name}")
        else:
            # Print details for manual review
            append_discovered_data(file_name, result)
            print(f"⚠️ No test data for {file_name}, added to discovered_data.json")
            # print(json.dumps(result, indent=2))
