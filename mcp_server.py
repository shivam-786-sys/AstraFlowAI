import os
import json
import re
from datetime import datetime

DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar_db.json")

def load_db():
    """Loads events from the JSON database safely."""
    if not os.path.exists(DATABASE_FILE):
        return []
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_db(data):
    """Saves events to the JSON database safely."""
    try:
        # Secure the directory
        db_dir = os.path.dirname(DATABASE_FILE)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

# List of tools complying with the Model Context Protocol (MCP) tool schema
MCP_TOOLS = [
    {
        "name": "schedule_event",
        "description": "Schedules a calendar block (study session, task, exam, or leisure event) into the system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the calendar event"},
                "start": {"type": "string", "description": "Start datetime in YYYY-MM-DD HH:MM format"},
                "end": {"type": "string", "description": "End datetime in YYYY-MM-DD HH:MM format"},
                "description": {"type": "string", "description": "Detailed description of the activity"},
                "category": {
                    "type": "string", 
                    "enum": ["study", "work", "life", "exam"],
                    "description": "The category classification of the activity"
                }
            },
            "required": ["title", "start", "end", "category"]
        }
    },
    {
        "name": "optimize_priority",
        "description": "Optimizes a list of tasks using Eisenhower Matrix priority logic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Task name"},
                            "urgency": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Urgency rating from 1 (low) to 5 (high)"},
                            "importance": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Importance rating from 1 (low) to 5 (high)"}
                        },
                        "required": ["name", "urgency", "importance"]
                    }
                }
            },
            "required": ["tasks"]
        }
    },
    {
        "name": "generate_study_cards",
        "description": "Generates flashcards from subject notes for active study preparation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Subject name"},
                "content": {"type": "string", "description": "Notes or raw topic text to extract cards from"}
            },
            "required": ["subject", "content"]
        }
    }
]

def handle_schedule_event(args):
    """MCP Tool Handler: schedule_event"""
    title = args.get("title")
    start = args.get("start")
    end = args.get("end")
    description = args.get("description", "")
    category = args.get("category", "study")
    
    # Input validation
    if not title or not start or not end:
        return {"success": False, "error": "Missing required fields: title, start, end, category"}
        
    # Format verification
    date_regex = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$"
    if not re.match(date_regex, start) or not re.match(date_regex, end):
        return {"success": False, "error": "Dates must match YYYY-MM-DD HH:MM format"}
        
    db = load_db()
    
    # Check for calendar overlap
    try:
        s_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        e_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        if s_dt >= e_dt:
            return {"success": False, "error": "Start date must be prior to end date"}
    except ValueError:
        return {"success": False, "error": "Invalid date format parsed"}
        
    conflicts = []
    for ev in db:
        try:
            ev_s = datetime.strptime(ev["start"], "%Y-%m-%d %H:%M")
            ev_e = datetime.strptime(ev["end"], "%Y-%m-%d %H:%M")
            # Overlap checking
            if s_dt < ev_e and e_dt > ev_s:
                conflicts.append(ev["title"])
        except ValueError:
            continue
            
    if conflicts:
        conflict_msg = f"Schedule warning: conflict detected with existing event(s) '{', '.join(conflicts)}'."
    else:
        conflict_msg = "No schedule conflict detected."

    new_event = {
        "id": len(db) + 1,
        "title": title,
        "start": start,
        "end": end,
        "description": description,
        "category": category,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    db.append(new_event)
    save_db(db)
    
    return {
        "success": True,
        "message": f"Successfully scheduled '{title}' under category '{category}'.",
        "conflict_info": conflict_msg,
        "event": new_event
    }

def handle_optimize_priority(args):
    """MCP Tool Handler: optimize_priority"""
    tasks = args.get("tasks")
    if not isinstance(tasks, list):
        return {"success": False, "error": "Tasks must be a list of task objects"}
        
    optimized_tasks = []
    for t in tasks:
        name = t.get("name")
        urgency = int(t.get("urgency", 3))
        importance = int(t.get("importance", 3))
        
        # Calculate matrix classification
        # Urgent & Important (urgency >= 3, importance >= 3) -> Do First (P1)
        # Important but Not Urgent (urgency < 3, importance >= 3) -> Schedule (P2)
        # Urgent but Not Important (urgency >= 3, importance < 3) -> Delegate (P3)
        # Neither (urgency < 3, importance < 3) -> Eliminate (P4)
        if urgency >= 3 and importance >= 3:
            quadrant = "Do First (Quadrant I)"
            priority_score = 1
        elif urgency < 3 and importance >= 3:
            quadrant = "Schedule (Quadrant II)"
            priority_score = 2
        elif urgency >= 3 and importance < 3:
            quadrant = "Delegate (Quadrant III)"
            priority_score = 3
        else:
            quadrant = "Eliminate (Quadrant IV)"
            priority_score = 4
            
        optimized_tasks.append({
            "name": name,
            "urgency": urgency,
            "importance": importance,
            "quadrant": quadrant,
            "priority_score": priority_score
        })
        
    # Sort tasks by priority score (ascending) and then by total weight (descending)
    optimized_tasks.sort(key=lambda x: (x["priority_score"], -(x["urgency"] + x["importance"])))
    
    return {
        "success": True,
        "optimized_tasks": optimized_tasks
    }

def handle_generate_study_cards(args):
    """MCP Tool Handler: generate_study_cards"""
    subject = args.get("subject", "General Study")
    content = args.get("content", "")
    
    if not content:
        return {"success": False, "error": "Content cannot be empty for card generation"}
        
    # Heuristic card generation from content
    # Look for sentences containing key concept triggers like "is", "defines", "means", "important"
    sentences = re.split(r'(?<=[.!?])\s+', content)
    cards = []
    
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if not sent:
            continue
            
        # Match pattern "X is Y" or "X refers to Y" or "X defines Y"
        match = re.search(r'\b([\w\s]{3,20})\s+(?:is|refers to|defines|means)\s+([^.]+)', sent, re.IGNORECASE)
        if match:
            term = match.group(1).strip().capitalize()
            definition = match.group(2).strip()
            cards.append({
                "id": len(cards) + 1,
                "front": f"What is {term}?",
                "back": f"{term} is {definition}."
            })
        elif len(sent) > 10 and len(cards) < 4:
            # Fallback cards if no matches
            cards.append({
                "id": len(cards) + 1,
                "front": f"Key Concept {len(cards) + 1} from study text",
                "back": sent
            })
            
    # Default cards if nothing extracted
    if not cards:
        cards = [
            {"id": 1, "front": f"Key concept in {subject}", "back": "Active review definitions based on notes."},
            {"id": 2, "front": "Primary topic structure", "back": "Break down into sub-topics and revise daily."}
        ]
        
    return {
        "success": True,
        "subject": subject,
        "flashcards": cards
    }

def call_mcp_tool(tool_name, args):
    """Dispatcher for MCP Server tool calls."""
    if tool_name == "schedule_event":
        return handle_schedule_event(args)
    elif tool_name == "optimize_priority":
        return handle_optimize_priority(args)
    elif tool_name == "generate_study_cards":
        return handle_generate_study_cards(args)
    else:
        return {"success": False, "error": f"Tool '{tool_name}' not found."}
