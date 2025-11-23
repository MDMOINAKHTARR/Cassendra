import os
import json
import random
from typing import TypedDict, List, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# --- State Definition ---
class AgentState(TypedDict):
    claim: str
    hypothesis: str
    sources: List[str]
    confidence: int
    contradiction_found: bool
    evidence: str
    kill_score: int
    status: str

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

import re
import json

def extract_json(text):
    try:
        # Find JSON block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except:
        return {}

# --- Agent 1: The Journalist (Builder) ---
def journalist_node(state: AgentState):
    print(f"\n[JOURNALIST] Researching claim: '{state['claim']}'")
    
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = tavily.search(query=state['claim'], search_depth="advanced", max_results=5)
        
        sources = [result['url'] for result in response['results']]
        context = "\n".join([r['content'] for r in response['results']])
        
        # Use Gemini to generate a hypothesis
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
        prompt = f"""
        You are a Journalist. Analyze these search results about the claim: "{state['claim']}".
        
        Search Results:
        {context}
        
        Task:
        1. Formulate a clear hypothesis about whether the claim is true or false based ONLY on these results.
        2. Assign a confidence score (0-100).
        
        Output format: JSON {{ "hypothesis": "string", "confidence": int }}
        """
        msg = HumanMessage(content=prompt)
        ai_msg = llm.invoke([msg])
        
        data = extract_json(ai_msg.content)
        
        hypothesis = data.get("hypothesis", "Analysis failed")
        confidence = data.get("confidence", 0)
            
    except Exception as e:
        print(f"[JOURNALIST] Error: {e}")
        hypothesis = f"Error during research: {e}"
        sources = []
        confidence = 0
    
    print(f"[JOURNALIST] Hypothesis: {hypothesis}")
    print(f"[JOURNALIST] Confidence: {confidence}")
    print(f"[JOURNALIST] Sources: {sources}")
    
    return {
        "hypothesis": hypothesis,
        "sources": sources,
        "confidence": confidence,
        "status": "researched"
    }

# --- Agent 2: The Editor (Skeptic) ---
def editor_node(state: AgentState):
    print(f"\n[EDITOR] Auditing hypothesis: '{state['hypothesis']}'")
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
        
        prompt = f"""
        You are a Skeptical Editor. Your job is to destroy this hypothesis.
        
        Hypothesis: "{state['hypothesis']}"
        Claim: "{state['claim']}"
        
        Task:
        1. Identify 3 specific "Kill Queries" that could disprove this. (e.g., check weather, check exif, check location history).
        2. Simulate the result of these checks based on common sense or the hypothesis itself (if it sounds fake).
        3. Decide if there is a contradiction.
        4. Assign a "Kill Score" (0-100), where 100 means definitely debunked.
        
        Output format: JSON {{ "contradiction_found": bool, "evidence": "string", "kill_score": int }}
        """
        
        msg = HumanMessage(content=prompt)
        ai_msg = llm.invoke([msg])
        
        data = extract_json(ai_msg.content)
        
        contradiction = data.get("contradiction_found", False)
        evidence = data.get("evidence", "No evidence provided.")
        kill_score = data.get("kill_score", 0)
        
    except Exception as e:
        print(f"[EDITOR] Error: {e}")
        contradiction = False
        evidence = f"Error during audit: {e}"
        kill_score = 0
        
    print(f"[EDITOR] Evidence: {evidence}")
    print(f"[EDITOR] Kill Score: {kill_score}/100")
    
    return {
        "contradiction_found": contradiction,
        "evidence": evidence,
        "kill_score": kill_score,
        "status": "audited"
    }

from neo4j import GraphDatabase

# --- Agent 3: The Archivist (Visualizer) ---
def archivist_node(state: AgentState):
    print(f"\n[ARCHIVIST] Updating Truth Graph...")
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password or "xxxx" in password:
        print("[ARCHIVIST] WARNING: Neo4j password not set. Skipping DB update.")
        return {"status": "skipped_db"}

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        def update_graph(tx, state):
            # Create Claim Node
            tx.run("MERGE (c:Claim {text: $claim}) SET c.status = 'VERIFYING'", claim=state['claim'])
            
            # Create Source Nodes
            for source in state['sources']:
                tx.run("""
                    MATCH (c:Claim {text: $claim})
                    MERGE (s:Source {url: $url})
                    MERGE (s)-[:SUPPORTS]->(c)
                """, claim=state['claim'], url=source)
            
            # Handle Contradiction
            if state['contradiction_found']:
                tx.run("""
                    MATCH (c:Claim {text: $claim})
                    SET c.status = 'DEBUNKED', c.color = '#ff0000'
                    MERGE (e:Evidence {text: $evidence})
                    MERGE (e)-[:CONTRADICTS]->(c)
                """, claim=state['claim'], evidence=state['evidence'])
                print(f"[ARCHIVIST] MARKED CLAIM AS DEBUNKED (RED NODE).")
            else:
                tx.run("""
                    MATCH (c:Claim {text: $claim})
                    SET c.status = 'VERIFIED', c.color = '#00ff00'
                """, claim=state['claim'])
                print(f"[ARCHIVIST] MARKED CLAIM AS VERIFIED (GREEN NODE).")

        with driver.session() as session:
            session.execute_write(update_graph, state)
            
        driver.close()
        final_status = "DEBUNKED" if state['contradiction_found'] else "VERIFIED"
        
    except Exception as e:
        print(f"[ARCHIVIST] Error updating Neo4j: {e}")
        final_status = "error"
    
    return {"status": final_status}

# --- Decision Logic ---
def should_continue(state: AgentState) -> Literal["archivist"]:
    # In this simple flow, we always go to the archivist after the editor
    return "archivist"

# --- Workflow Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("journalist", journalist_node)
workflow.add_node("editor", editor_node)
workflow.add_node("archivist", archivist_node)

workflow.set_entry_point("journalist")

workflow.add_edge("journalist", "editor")
workflow.add_edge("editor", "archivist")
workflow.add_edge("archivist", END)

app = workflow.compile()

# --- Execution ---
if __name__ == "__main__":
    print("\n--- CASSANDRA: Autonomous OSINT Verification Engine ---")
    print("Enter a rumor, news headline, or claim to verify.")
    user_claim = input(">>> Claim: ")
    
    if not user_claim.strip():
        print("No claim entered. Exiting.")
        exit()

    initial_input = {"claim": user_claim, "status": "new"}
    
    print(f"\n[ORCHESTRATOR] Spawning agents for: '{user_claim}'...\n")
    for output in app.stream(initial_input):
        pass
    print("\n--- VERIFICATION COMPLETE ---")
    print("Check your Neo4j Dashboard for the Truth Graph.")
