import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print(f"Testing Gemini Direct with key: {api_key[:5]}...{api_key[-5:]}")

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Sending request...")
    response = model.generate_content("Hello, are you working?")
    print("Response received:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
