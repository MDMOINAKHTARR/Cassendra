import os
import json
import asyncio
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import re

# Load environment variables
load_dotenv()

# --- ANSI Color Codes for Terminal ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    """Print ASCII art banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ █████╗ ███████╗███████╗ █████╗ ███╗   ██╗██████╗   ║
║  ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║██╔══██╗  ║
║  ██║     ███████║███████╗███████╗███████║██╔██╗ ██║██║  ██║  ║
║  ██║     ██╔══██║╚════██║╚════██║██╔══██║██║╚██╗██║██║  ██║  ║
║  ╚██████╗██║  ██║███████║███████║██║  ██║██║ ╚████║██████╔╝  ║
║   ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝   ║
║                                                               ║
║         Autonomous OSINT Verification Engine                 ║
║              Terminal-Based Truth Detector                    ║
╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)

def print_section(title, color=Colors.CYAN):
    """Print a section header"""
    print(f"\n{color}{Colors.BOLD}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{Colors.ENDC}\n")

def print_agent_status(agent_name, status, color=Colors.BLUE):
    """Print agent status update"""
    print(f"{color}{Colors.BOLD}[{agent_name}]{Colors.ENDC} {status}")

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

def extract_json(text):
    """Extract JSON from LLM response"""
    try:
        # Find JSON block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except:
        return {}

# --- Agent 1: The Journalist (Builder) ---
async def journalist_node(state: AgentState):
    """Research the claim and formulate hypothesis"""
    print_section("🔍 JOURNALIST - RESEARCH PHASE", Colors.BLUE)
    print_agent_status("JOURNALIST", f"Researching claim: '{state['claim']}'", Colors.BLUE)
    
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        print_agent_status("JOURNALIST", "Searching the web for evidence...", Colors.BLUE)
        response = tavily.search(query=state['claim'], search_depth="advanced", max_results=5)
        
        sources = [result['url'] for result in response['results']]
        context = "\n".join([r['content'] for r in response['results']])
        
        print_agent_status("JOURNALIST", f"Found {len(sources)} sources", Colors.BLUE)
        for i, source in enumerate(sources, 1):
            print(f"  {Colors.CYAN}[{i}]{Colors.ENDC} {source[:80]}...")
        
        # Use Gemini to generate a hypothesis
        print_agent_status("JOURNALIST", "Analyzing evidence with AI...", Colors.BLUE)
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
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {e}")
        hypothesis = f"Error during research: {e}"
        sources = []
        confidence = 0
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}HYPOTHESIS:{Colors.ENDC} {hypothesis}")
    print(f"{Colors.YELLOW}CONFIDENCE:{Colors.ENDC} {confidence}%")
    
    return {
        "hypothesis": hypothesis,
        "sources": sources,
        "confidence": confidence,
        "status": "researched"
    }

# --- Agent 2: The Editor (Skeptic) ---
async def editor_node(state: AgentState):
    """Audit the hypothesis and look for contradictions"""
    print_section("⚡ EDITOR - SKEPTICAL AUDIT", Colors.YELLOW)
    print_agent_status("EDITOR", f"Auditing hypothesis...", Colors.YELLOW)
    
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
        
        print_agent_status("EDITOR", "Running adversarial analysis...", Colors.YELLOW)
        msg = HumanMessage(content=prompt)
        ai_msg = llm.invoke([msg])
        
        data = extract_json(ai_msg.content)
        
        contradiction = data.get("contradiction_found", False)
        evidence = data.get("evidence", "No evidence provided.")
        kill_score = data.get("kill_score", 0)
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {e}")
        contradiction = False
        evidence = f"Error during audit: {e}"
        kill_score = 0
    
    print(f"\n{Colors.BOLD}AUDIT EVIDENCE:{Colors.ENDC} {evidence}")
    print(f"{Colors.RED if kill_score > 50 else Colors.GREEN}KILL SCORE:{Colors.ENDC} {kill_score}/100")
    
    return {
        "contradiction_found": contradiction,
        "evidence": evidence,
        "kill_score": kill_score,
        "status": "audited"
    }

# --- Agent 3: The Archivist (Database) ---
async def archivist_node(state: AgentState):
    """Archive findings to Neo4j Truth Graph"""
    print_section("📊 ARCHIVIST - TRUTH GRAPH UPDATE", Colors.CYAN)
    print_agent_status("ARCHIVIST", "Updating Truth Graph database...", Colors.CYAN)
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password or "xxxx" in password:
        print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} Neo4j password not configured. Skipping database update.")
        print(f"{Colors.CYAN}[INFO]{Colors.ENDC} Configure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env to enable graph storage.")
        final_status = "DEBUNKED" if state.get('contradiction_found') else "VERIFIED"
    else:
        try:
            from neo4j import GraphDatabase
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
                else:
                    tx.run("""
                        MATCH (c:Claim {text: $claim})
                        SET c.status = 'VERIFIED', c.color = '#00ff00'
                    """, claim=state['claim'])

            with driver.session() as session:
                session.execute_write(update_graph, state)
                
            driver.close()
            final_status = "DEBUNKED" if state['contradiction_found'] else "VERIFIED"
            print_agent_status("ARCHIVIST", f"Graph updated successfully - Status: {final_status}", Colors.GREEN)
            
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.ENDC} Neo4j error: {e}")
            final_status = "error"
    
    return {"status": final_status}

# --- Workflow Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("journalist", journalist_node)
workflow.add_node("editor", editor_node)
workflow.add_node("archivist", archivist_node)

workflow.set_entry_point("journalist")

workflow.add_edge("journalist", "editor")
workflow.add_edge("editor", "archivist")
workflow.add_edge("archivist", END)

graph_app = workflow.compile()

# --- Main CLI Function ---
async def verify_claim(claim: str):
    """Run the verification workflow for a given claim"""
    initial_input = {"claim": claim, "status": "new"}
    
    print_section("🚀 VERIFICATION WORKFLOW STARTED", Colors.GREEN)
    print(f"{Colors.BOLD}CLAIM:{Colors.ENDC} {claim}\n")
    
    final_state = {}
    async for output in graph_app.astream(initial_input):
        # Store final state from each node
        for node_name, node_output in output.items():
            final_state.update(node_output)
    
    # Print final verdict
    print_section("✅ VERIFICATION COMPLETE", Colors.GREEN)
    
    verdict = "DEBUNKED" if final_state.get('contradiction_found') else "VERIFIED"
    verdict_color = Colors.RED if verdict == "DEBUNKED" else Colors.GREEN
    
    print(f"{Colors.BOLD}FINAL VERDICT:{Colors.ENDC} {verdict_color}{verdict}{Colors.ENDC}")
    print(f"{Colors.BOLD}CONFIDENCE:{Colors.ENDC} {final_state.get('confidence', 0)}%")
    print(f"{Colors.BOLD}KILL SCORE:{Colors.ENDC} {final_state.get('kill_score', 0)}/100")
    
    if final_state.get('sources'):
        print(f"\n{Colors.BOLD}SOURCES ({len(final_state['sources'])}):{Colors.ENDC}")
        for i, source in enumerate(final_state['sources'], 1):
            print(f"  [{i}] {source}")
    
    print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}\n")

# --- Main Entry Point ---
if __name__ == "__main__":
    print_banner()
    
    print(f"{Colors.BOLD}The CASSANDRA Engine{Colors.ENDC} uses a multi-agent adversarial system:")
    print(f"  {Colors.BLUE}• Journalist{Colors.ENDC} - Researches and builds hypothesis")
    print(f"  {Colors.YELLOW}• Editor{Colors.ENDC} - Skeptically audits for contradictions")
    print(f"  {Colors.CYAN}• Archivist{Colors.ENDC} - Archives findings to Truth Graph")
    
    print(f"\n{Colors.GREEN}Enter a claim, rumor, or news headline to verify.{Colors.ENDC}")
    print(f"{Colors.YELLOW}Press Ctrl+C to exit.{Colors.ENDC}\n")
    
    try:
        while True:
            user_claim = input(f"{Colors.BOLD}{Colors.CYAN}>>> CLAIM: {Colors.ENDC}").strip()
            
            if not user_claim:
                print(f"{Colors.YELLOW}[!] No claim entered. Please enter a claim.{Colors.ENDC}\n")
                continue
            
            # Run verification
            asyncio.run(verify_claim(user_claim))
            
            print(f"\n{Colors.GREEN}Ready for next claim...{Colors.ENDC}\n")
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}{'='*70}")
        print(f"  Thank you for using CASSANDRA!")
        print(f"  Truth Graph preserved in Neo4j database.")
        print(f"{'='*70}{Colors.ENDC}\n")
