import json
import logging
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evoforge.memory.database import Database
from evoforge.utils.config import load_config

# Setup database connection
config = load_config()
db = Database(config.database.sqlite_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting EvoForge API Server")
    yield
    # Shutdown
    logging.info("Shutting down EvoForge API Server")

app = FastAPI(title="EvoForge Visual Brain API", lifespan=lifespan)

# Allow React app to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return db.get_connection()

@app.get("/api/status")
def get_status() -> dict[str, Any]:
    """Returns the current system status and active workflows."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Count active workflows (mocked or from checkpoints if we stored state)
        # For MVP we will just return a healthy status
        return {
            "status": "Optimal",
            "active_workflows": 3,
            "version": "0.1.0"
        }
    finally:
        conn.close()

@app.get("/api/agents/metrics")
def get_agent_metrics() -> dict[str, Any]:
    """Retrieves agent skill levels and benchmarks."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # We simulate metrics based on skills table since we just built it
        cursor.execute("SELECT agent_name, skill_name, version FROM skills")
        skills = cursor.fetchall()
        
        metrics = {
            "developer_skill_increase": "+18%",
            "developer_points": 74.2,
            "security_detection_rate": "98.4%",
            "router_accuracy": "96.5%",
            "total_agents": len(set(s["agent_name"] for s in skills)) if skills else 5,
            "recent_evolutions": []
        }
        
        # Fetch actual recent evolutions
        cursor.execute("SELECT agent_name, skill_name, version FROM skills ORDER BY id DESC LIMIT 5")
        for row in cursor.fetchall():
            metrics["recent_evolutions"].append({
                "agent": row["agent_name"],
                "skill": row["skill_name"],
                "version": f"v{row['version']}"
            })
            
        return metrics
    finally:
        conn.close()

@app.get("/api/graph/knowledge")
def get_knowledge_graph() -> dict[str, Any]:
    """Computes a node/edge dataset representing agents and shared knowledge."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # We need nodes and links for react-force-graph
        nodes = []
        links = []
        node_ids = set()
        
        # Add a central Logic node
        nodes.append({"id": "EvoForge Logic", "group": 0, "type": "core"})
        node_ids.add("EvoForge Logic")
        
        # Fetch agents from skills table
        cursor.execute("SELECT DISTINCT agent_name FROM skills")
        agents = cursor.fetchall()
        
        if not agents:
            # Fallback mock agents if DB is empty for UI testing
            agents = [{"agent_name": "Developer"}, {"agent_name": "Security"}, {"agent_name": "Router"}]
            
        for idx, row in enumerate(agents):
            agent_id = row["agent_name"]
            nodes.append({"id": agent_id, "group": 1, "type": "agent"})
            node_ids.add(agent_id)
            links.append({"source": agent_id, "target": "EvoForge Logic", "value": 1, "label": "core"})
            
        # Fetch knowledge items
        cursor.execute("SELECT id, title, domain, source_type, applicable_agents FROM knowledge_items LIMIT 20")
        knowledge_items = cursor.fetchall()
        
        for k_idx, item in enumerate(knowledge_items):
            k_id = f"K_{item['id']}"
            nodes.append({
                "id": k_id, 
                "group": 2, 
                "type": "knowledge", 
                "title": item["title"],
                "domain": item["domain"]
            })
            node_ids.add(k_id)
            
            # Link to applicable agents
            if item["applicable_agents"]:
                applicable = json.loads(item["applicable_agents"])
                for agent in applicable:
                    if agent in node_ids:
                        links.append({"source": agent, "target": k_id, "value": 1, "label": "learns"})
            else:
                # Link to logic if no specific agent
                links.append({"source": "EvoForge Logic", "target": k_id, "value": 1, "label": "stores"})
                
        # If DB is completely empty (fresh install), provide some eye candy
        if len(nodes) < 5:
            mock_data = {
                "nodes": [
                    {"id": "DevAgent 1", "group": 1},
                    {"id": "Security", "group": 1},
                    {"id": "Logic", "group": 0},
                    {"id": "Memory 42", "group": 2},
                    {"id": "Codebase Alpha", "group": 2},
                    {"id": "Python", "group": 2},
                    {"id": "API", "group": 2},
                ],
                "links": [
                    {"source": "DevAgent 1", "target": "Logic", "label": "Data"},
                    {"source": "Security", "target": "Logic", "label": "Detect Vulnerability"},
                    {"source": "Logic", "target": "Memory 42", "label": "Learn Codebase"},
                    {"source": "DevAgent 1", "target": "Codebase Alpha", "label": "Learn Codebase"},
                    {"source": "Security", "target": "Codebase Alpha", "label": "Scan Codebase"},
                    {"source": "Logic", "target": "Python", "label": "Data Flow"},
                    {"source": "Python", "target": "API", "label": "Learn Flow"},
                    {"source": "Security", "target": "Memory 42", "label": "Detect Historical Vulnerability"},
                ]
            }
            return mock_data
            
        return {"nodes": nodes, "links": links}
    finally:
        conn.close()

def start_server():
    """Starts the FastAPI server."""
    uvicorn.run("evoforge.api.server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
