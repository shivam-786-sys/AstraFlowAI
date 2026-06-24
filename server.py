import os
import json
import subprocess
import re
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

import mcp_server  # Local MCP server functions
import agents      # Multi-agent simulation

app = FastAPI(title="AstraFlow Dashboard Server", version="1.0.0")

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(WORKSPACE_DIR, "static")

# Ensure static directories exist
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

# ----------------------------------------------------
# Pydantic Schemas for Input Validation (Security)
# ----------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000, description="User prompt or task brief")

class ExportRequest(BaseModel):
    events: List[Dict[str, Any]] = Field(..., description="List of scheduled events to export")
    filename: str = Field("schedule.ics", description="Relative filename to write (restricted to workspace)")

# ----------------------------------------------------
# API Routes
# ----------------------------------------------------

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Runs the ADK offline multi-agent workflow simulation
    based on the validated user prompt.
    """
    # Sanitize user prompt to prevent prompt injections
    sanitized_prompt = re.sub(r'[<>{}]', '', request.message)
    
    workflow = agents.AstraFlowWorkflow()
    try:
        result = workflow.run(sanitized_prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent System Error: {str(e)}")

@app.get("/api/calendar")
async def get_calendar():
    """Retrieves all scheduled calendar events from the local database."""
    events = mcp_server.load_db()
    return {"status": "success", "events": events}

@app.post("/api/calendar/clear")
async def clear_calendar():
    """Clears all events in the local database."""
    mcp_server.save_db([])
    return {"status": "success", "message": "Calendar database cleared."}

@app.get("/api/status")
async def status_endpoint():
    """Server diagnostics and dependency status."""
    db_path = mcp_server.DATABASE_FILE
    db_exists = os.path.exists(db_path)
    db_size = os.path.getsize(db_path) if db_exists else 0
    
    return {
        "status": "online",
        "workspace": WORKSPACE_DIR,
        "database": {
            "path": db_path,
            "exists": db_exists,
            "events_count": len(mcp_server.load_db()),
            "size_bytes": db_size
        },
        "mcp_server": {
            "tools_registered": len(mcp_server.MCP_TOOLS),
            "status": "active"
        }
    }

@app.post("/api/export")
async def export_endpoint(request: ExportRequest):
    """
    Executes the CLI agent skill tool (`cli_tool.py`) securely via subprocess.
    Verifies that the target path does not bypass the workspace constraints.
    """
    # Security Check: Prevent directory traversal on filename
    clean_filename = os.path.basename(request.filename)
    if not clean_filename.endswith(".ics"):
        clean_filename += ".ics"
        
    relative_target = os.path.join("exports", clean_filename)
    absolute_target = os.path.abspath(os.path.join(WORKSPACE_DIR, relative_target))
    
    # Path traversal validation
    if not absolute_target.startswith(WORKSPACE_DIR):
        raise HTTPException(status_code=400, detail="Security Exception: Target path is outside the workspace.")
        
    # Serialize events to JSON string
    events_json = json.dumps(request.events)
    
    # Run the external CLI skill safely via subprocess
    cli_path = os.path.join(WORKSPACE_DIR, "cli_tool.py")
    
    cmd = [
        "python",
        cli_path,
        "--action", "export-ics",
        "--input", events_json,
        "--output", absolute_target
    ]
    
    try:
        # Run process with timeout to prevent hangs (Safe execution)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10.0,
            cwd=WORKSPACE_DIR
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"CLI Tool execution failed: {result.stderr}")
            
        return {
            "status": "success",
            "message": result.stdout.strip(),
            "file_path": relative_target,
            "filename": clean_filename
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="CLI Tool execution timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLI subprocess launch error: {str(e)}")

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Downloads exported calendar file safely."""
    # Enforce safe path lookup
    clean_filename = os.path.basename(filename)
    file_path = os.path.abspath(os.path.join(WORKSPACE_DIR, "exports", clean_filename))
    
    if not file_path.startswith(WORKSPACE_DIR) or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested file not found.")
        
    return FileResponse(file_path, filename=clean_filename, media_type="text/calendar")

# ----------------------------------------------------
# Serve Static Frontend Files
# ----------------------------------------------------

@app.get("/")
async def get_index():
    """Serves the main entry dashboard interface."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_file):
        raise HTTPException(status_code=404, detail="Frontend build files not found. Generate static assets.")
    return FileResponse(index_file)

# Mount remaining static folder files (JS, CSS)
app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
