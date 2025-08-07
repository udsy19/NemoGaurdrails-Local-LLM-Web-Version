import requests
import json

url = "http://localhost:8891/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer EMPTY"  # Your proxy might not check this
}

data = {
    "model": "gpt-4",  # Change if needed
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "what the actual fuck"}
    ]
}

# Send POST request
try:
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)

    # Debug print: show entire JSON response
    print("==== RAW JSON RESPONSE ====")
    print(response.json())

    # Safely extract fields
    try:
        res_json = response.json()
        if "choices" in res_json and "message" in res_json["choices"][0]:
            print("\n==== ASSISTANT RESPONSE ====")
            print(res_json["choices"][0]["message"]["content"])
        elif "choices" in res_json and "text" in res_json["choices"][0]:
            print("\n==== ASSISTANT RESPONSE (text field) ====")
            print(res_json["choices"][0]["text"])
        else:
            print("Unexpected response format! Check keys above.")
    except Exception as e:
        print(f"Error parsing response: {e}")
        
except requests.exceptions.ConnectError:
    print("❌ Connection failed - please start the backend server first")
    print("Run: python app/main.py")
except requests.exceptions.Timeout:
    print("❌ Request timed out - server may be overloaded")
except Exception as e:
    print(f"❌ Error: {e}")