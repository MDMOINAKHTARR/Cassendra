# CASSANDRA: Autonomous OSINT Verification Engine

**CASSANDRA** is a multi-agent adversarial system designed to verify viral rumors and news claims. It uses a team of AI agents to research, audit, and archive the truth in a powerful terminal interface.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- API Keys (see Configuration below)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run CASSANDRA
python main.py
```

The terminal interface will guide you through claim verification.

## 🤖 The Agents

CASSANDRA uses three AI agents working together:

1. **The Journalist** (Builder):
   - Searches the web using **Tavily API**
   - Uses **Gemini 2.0 Flash** to formulate a hypothesis
   - Assigns a confidence score

2. **The Editor** (Skeptic):
   - Audits the Journalist's hypothesis
   - Looks for contradictions using adversarial reasoning
   - Assigns a "Kill Score" to debunk false claims

3. **The Archivist** (Database):
   - Stores findings in **Neo4j AuraDB** (optional)
   - Maintains a "Truth Graph" of verified/debunked claims

## 🛠 Configuration

Create a `.env` file in the project root with the following API keys:

```env
# Required: For AI reasoning
GOOGLE_API_KEY=your_google_api_key_here

# Required: For web search
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: For graph database (skip if not using Neo4j)
NEO4J_URI=your_neo4j_uri_here
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
```

### Getting API Keys

- **Google API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Tavily API Key**: Sign up at [Tavily](https://tavily.com)
- **Neo4j** (Optional): Create free database at [Neo4j Aura](https://neo4j.com/cloud/aura/)

## 💡 Usage

1. Run `python main.py`
2. Enter a rumor, news headline, or claim when prompted
3. Watch the AI agents investigate in real-time
4. Review the final verdict (VERIFIED or DEBUNKED)
5. Enter another claim or press Ctrl+C to exit

### Example Session

```
>>> CLAIM: The Eiffel Tower was sold to a scrap dealer in 1925

🔍 JOURNALIST - RESEARCH PHASE
[JOURNALIST] Found 5 sources
HYPOTHESIS: Victor Lustig, a con artist, successfully sold the Eiffel Tower...
CONFIDENCE: 85%

⚡ EDITOR - SKEPTICAL AUDIT
KILL SCORE: 15/100

✅ VERIFICATION COMPLETE
FINAL VERDICT: VERIFIED
```

## 📊 Truth Graph (Optional)

If you configure Neo4j credentials, CASSANDRA will maintain a persistent "Truth Graph" where:
- **Green nodes** = Verified claims
- **Red nodes** = Debunked claims
- **Edges** = Sources and evidence

Access your Neo4j Dashboard to visualize the graph.

## 🔧 Troubleshooting

**Missing API Keys**: Ensure your `.env` file contains valid `GOOGLE_API_KEY` and `TAVILY_API_KEY`.

**Neo4j Warnings**: Neo4j is optional. The system will work without it, just skip graph storage.

## 📝 License

MIT License - Feel free to use and modify!
