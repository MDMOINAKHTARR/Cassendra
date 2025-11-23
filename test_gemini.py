import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"Testing Gemini with key: {api_key[:5]}...{api_key[-5:]}")

try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    msg = HumanMessage(content="Hello, are you working?")
    print("Sending request...")
    response = llm.invoke([msg])
    print("Response received:")
    print(response.content)
except Exception as e:
    print(f"Error: {e}")
