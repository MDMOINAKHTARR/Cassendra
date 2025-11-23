import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD")

print(f"Testing connection to: {uri}")
print(f"User: {user}")
print(f"Password: {password[:5]}...")

try:
    print(f"Attempting connection with neo4j+s...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print("Connection SUCCESS with neo4j+s!")
    driver.close()
except Exception as e:
    print(f"Connection FAILED with neo4j+s: {e}")
    
    # Try ssc
    try:
        print(f"Attempting connection with neo4j+ssc (self-signed)...")
        uri_ssc = uri.replace("neo4j+s://", "neo4j+ssc://")
        driver = GraphDatabase.driver(uri_ssc, auth=(user, password))
        driver.verify_connectivity()
        print("Connection SUCCESS with neo4j+ssc!")
        driver.close()
    except Exception as e2:
        print(f"Connection FAILED with neo4j+ssc: {e2}")
