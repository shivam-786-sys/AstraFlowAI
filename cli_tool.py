#!/usr/bin/env python3
import sys
import os
import argparse
import json
import re
from datetime import datetime

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def validate_safe_path(target_path):
    """
    Validates that the target path remains strictly within the workspace directory,
    preventing path traversal attacks.
    """
    abs_path = os.path.abspath(target_path)
    # Check if the path starts with the workspace path
    if not abs_path.startswith(WORKSPACE_DIR):
        raise ValueError(f"Security Alert: Target path '{target_path}' lies outside the workspace directory.")
    
    # Check for disallowed characters in filenames
    filename = os.path.basename(abs_path)
    if not re.match(r'^[\w\-. ]+$', filename):
        raise ValueError(f"Security Alert: Filename '{filename}' contains unsafe characters.")
        
    # Restrict extensions to safe ones
    _, ext = os.path.splitext(filename)
    if ext.lower() not in ['.ics', '.md', '.json']:
        raise ValueError(f"Security Alert: Extension '{ext}' is not permitted for output generation.")
        
    return abs_path

def export_ics(events_json, output_file):
    """
    Parses events JSON and formats it into a standard iCalendar (ICS) format.
    """
    # Security check on output path
    safe_output_path = validate_safe_path(output_file)
    
    try:
        events = json.loads(events_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON payload provided. {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    if not isinstance(events, list):
        print("Error: Event list must be a JSON array.", file=sys.stderr)
        sys.exit(1)
        
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AstraFlow//Scheduler Skill//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    for i, event in enumerate(events):
        title = event.get("title", f"Event {i+1}").replace(",", "\\,").replace(";", "\\;")
        start_str = event.get("start") # Expected ISO 8601 or similar, e.g. YYYYMMDDTHHMMSS
        end_str = event.get("end")
        description = event.get("description", "").replace(",", "\\,").replace(";", "\\;")
        
        # Simple cleanup to format start/end as iCal date-times
        # If dates are in YYYY-MM-DD HH:MM format, we convert them
        def to_ical_dt(dt_str):
            if not dt_str:
                return datetime.now().strftime("%Y%m%dT%H%M%S")
            # Strip non-alphanumeric except T
            clean = re.sub(r'[^0-9T]', '', dt_str)
            if len(clean) == 8: # YYYYMMDD -> YYYYMMDDT120000
                return clean + "T120000"
            if len(clean) >= 14:
                return clean[:15] # Limit to YYYYMMDDTHHMMSS
            return clean
            
        dtstart = to_ical_dt(start_str)
        dtend = to_ical_dt(end_str)
        
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:astraflow-{int(datetime.now().timestamp())}-{i}@{datetime.now().strftime('%Y%m%d')}",
            f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{title}",
            f"DESCRIPTION:{description}",
            "END:VEVENT"
        ])
        
    ics_lines.append("END:VCALENDAR")
    
    # Write to safe path
    parent_dir = os.path.dirname(safe_output_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    with open(safe_output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ics_lines))
        
    print(f"Success: ICS file exported successfully to '{safe_output_path}'.")

def generate_summary(text_input, output_file, topic="Study Topic"):
    """
    Creates a formatted markdown study summary.
    """
    safe_output_path = validate_safe_path(output_file)
    
    if len(text_input) > 20000:
        raise ValueError("Security Alert: Input payload exceeds maximum limit of 20,000 characters.")
        
    # Standard template formatting
    markdown_content = f"""# AstraFlow Study Summary: {topic}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview & Key Objectives
{text_input}

## Study Guidelines
1. **Active Recall**: Convert sections of this summary into flashcards or self-quizzes.
2. **Spaced Repetition**: Re-evaluate this content in 1 day, 3 days, and then 1 week.
3. **Pomodoro Sprints**: Study each key section in focused 25-minute intervals.

---
*AstraFlow — Task Optimization & Study Planner System*
"""
    parent_dir = os.path.dirname(safe_output_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    with open(safe_output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content.strip())
        
    print(f"Success: Markdown summary exported successfully to '{safe_output_path}'.")

def main():
    parser = argparse.ArgumentParser(description="AstraFlow Skills CLI Utility")
    parser.add_argument("--action", required=True, choices=["export-ics", "generate-summary"], help="The skill action to execute")
    parser.add_argument("--input", required=True, help="Input content (JSON event array string for export-ics, text body for generate-summary)")
    parser.add_argument("--output", required=True, help="Relative or absolute path for the output file (restricted to workspace)")
    parser.add_argument("--topic", default="Study Topic", help="Topic name for study summary")
    
    args = parser.parse_args()
    
    try:
        if args.action == "export-ics":
            export_ics(args.input, args.output)
        elif args.action == "generate-summary":
            generate_summary(args.input, args.output, args.topic)
    except Exception as e:
        print(f"Execution Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
