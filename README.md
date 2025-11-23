# CASSANDRA: Autonomous OSINT Verification Engine

Cassandra is a multi-agent adversarial system designed to verify viral rumors and news claims. It uses a team of AI agents to research, audit, and archive the truth.

## 🚀 Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the System**:
    ```bash
    python main.py
    ```

3.  **Enter a Claim**:
    When prompted, type a claim you want to verify.
    > `>>> Claim: The Eiffel Tower is on fire`

4.  **View Results**:
    - Watch the terminal for agent deliberations.
    - Check your **Neo4j Dashboard** to see the knowledge graph growing.
    - Open `dashboard.html` for a visualization preview.

## 🤖 The Agents

1.  **The Journalist** (Builder):
    - Searches the web using **Tavily API**.
    - Uses **Gemini 2.0 Flash** to formulate a hypothesis.

2.  **The Editor** (Skeptic):
    - Audits the Journalist's hypothesis.
    - Looks for contradictions and assigns a "Kill Score".

3.  **The Archivist** (Visualizer):
    - Stores the findings in **Neo4j AuraDB**.
    - Creates nodes for Claims, Sources, and Evidence.

## 🛠 Configuration

The system uses a `.env` file for API keys:
- `TAVILY_API_KEY`: For web search.
- `GOOGLE_API_KEY`: For AI reasoning.
- `NEO4J_URI`, `USERNAME`, `PASSWORD`: For the graph database.
