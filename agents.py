import json
import os
import re
from datetime import datetime, timedelta
import mcp_server  # Local MCP server simulation

class AgentState:
    """Models session state for the multi-agent system."""
    def __init__(self):
        self.variables = {}
        self.history = []

class AgentSim:
    """Simulates an ADK Agent with local instruction-based execution."""
    def __init__(self, name, description, instruction):
        self.name = name
        self.description = description
        self.instruction = instruction

    def log_thought(self, message):
        return {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "type": "thought",
            "message": message
        }

    def log_tool_call(self, tool_name, args):
        return {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "type": "tool_call",
            "tool_name": tool_name,
            "arguments": args
        }

    def log_tool_response(self, response):
        return {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "type": "tool_response",
            "response": response
        }

    def log_output(self, message):
        return {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "type": "output",
            "message": message
        }

class AstraFlowWorkflow:
    """Orchestrates the offline multi-agent workflow graph."""
    def __init__(self):
        self.planner = AgentSim(
            name="PlannerAgent",
            description="Analyzes request and schedules task routing.",
            instruction="Parse the user's intent. Break it down into sub-plans for scheduling, studying, and optimization."
        )
        self.task_optimizer = AgentSim(
            name="TaskOptimizationAgent",
            description="Optimizes priorities using Eisenhower matrix logic.",
            instruction="Evaluate task urgency and importance. Call the prioritize tool to compute quadrants."
        )
        self.exam_study = AgentSim(
            name="ExamStudyAgent",
            description="Plans study blocks and flashcards.",
            instruction="Design study blocks and call mock card generation tools."
        )
        self.life_scheduler = AgentSim(
            name="LifeSchedulerAgent",
            description="Coordinates study and life events safely to avoid conflicts.",
            instruction="Run schedule event tool. Check calendar availability and verify conflicts."
        )

    def run(self, user_prompt: str):
        steps = []
        state = AgentState()
        state.variables["raw_prompt"] = user_prompt
        
        # ----------------------------------------------------
        # 1. START Node
        # ----------------------------------------------------
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "workflow_status",
            "message": "Workflow started. Initializing node: START"
        })

        # ----------------------------------------------------
        # 2. PlannerAgent Execution
        # ----------------------------------------------------
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "node_transition",
            "from_node": "START",
            "to_node": "PlannerAgent"
        })
        
        steps.append(self.planner.log_thought(f"Analyzing prompt: '{user_prompt}'"))
        
        # Extract subjects/exams
        subjects = re.findall(r'\b(chemistry|biology|physics|math|english|history|cs|programming)\b', user_prompt, re.IGNORECASE)
        subjects = list(set([s.capitalize() for s in subjects]))
        if not subjects:
            subjects = ["General Study"]
            
        steps.append(self.planner.log_thought(f"Extracted key subjects for planning: {subjects}"))
        
        # Extract events and times (e.g. gym, quiz)
        has_gym = "gym" in user_prompt.lower()
        has_quiz = "quiz" in user_prompt.lower() or "exam" in user_prompt.lower()
        
        steps.append(self.planner.log_output(
            f"Planner initialized. Created orchestrations:\n"
            f"- Route A: Optimize task hierarchy for {', '.join(subjects)}.\n"
            f"- Route B: Structure custom study blocks and active recall modules.\n"
            f"- Route C: Integrate life commitments (Gym: {has_gym}) into calendar."
        ))
        
        state.variables["subjects"] = subjects
        state.variables["has_gym"] = has_gym
        state.variables["has_quiz"] = has_quiz

        # ----------------------------------------------------
        # 3. TaskOptimizationAgent Execution
        # ----------------------------------------------------
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "node_transition",
            "from_node": "PlannerAgent",
            "to_node": "TaskOptimizationAgent"
        })
        
        steps.append(self.task_optimizer.log_thought("Evaluating task dependencies. Formulating task queue for Eisenhower Matrix analysis."))
        
        # Build tasks to prioritize
        tasks = []
        for sub in subjects:
            tasks.append({"name": f"Study {sub} core topics", "urgency": 4 if has_quiz else 2, "importance": 5})
            tasks.append({"name": f"Review {sub} mock cards", "urgency": 3, "importance": 4})
        if has_gym:
            tasks.append({"name": "Gym Workout Session", "urgency": 3, "importance": 3})
            
        tool_args = {"tasks": tasks}
        steps.append(self.task_optimizer.log_tool_call("optimize_priority", tool_args))
        
        # Call local MCP tool
        priority_res = mcp_server.call_mcp_tool("optimize_priority", tool_args)
        steps.append(self.task_optimizer.log_tool_response(priority_res))
        
        optimized_tasks = priority_res.get("optimized_tasks", [])
        state.variables["optimized_tasks"] = optimized_tasks
        
        steps.append(self.task_optimizer.log_output(
            f"Prioritization complete. Main urgent tasks identified: "
            f"'{', '.join([t['name'] for t in optimized_tasks if t['priority_score'] == 1])}'"
        ))

        # ----------------------------------------------------
        # 4. ExamStudyAgent Execution
        # ----------------------------------------------------
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "node_transition",
            "from_node": "TaskOptimizationAgent",
            "to_node": "ExamStudyAgent"
        })
        
        steps.append(self.exam_study.log_thought(f"Designing custom study cards and topics for: {subjects}."))
        
        flashcards_by_subject = {}
        for sub in subjects:
            notes_context = (
                f"{sub} is a critical subject area. Study focus includes definition of core terminology. "
                f"Formula sheet defines primary calculations. Important models outline the concepts."
            )
            card_args = {"subject": sub, "content": notes_context}
            steps.append(self.exam_study.log_tool_call("generate_study_cards", card_args))
            
            card_res = mcp_server.call_mcp_tool("generate_study_cards", card_args)
            steps.append(self.exam_study.log_tool_response(card_res))
            
            flashcards_by_subject[sub] = card_res.get("flashcards", [])
            
        state.variables["flashcards"] = flashcards_by_subject
        steps.append(self.exam_study.log_output(
            f"Active recall deck created. Generated {sum(len(c) for c in flashcards_by_subject.values())} active study cards."
        ))

        # ----------------------------------------------------
        # 5. LifeSchedulerAgent Execution
        # ----------------------------------------------------
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "node_transition",
            "from_node": "ExamStudyAgent",
            "to_node": "LifeSchedulerAgent"
        })
        
        steps.append(self.life_scheduler.log_thought("Beginning time block allocation. Scanning calendar database for collisions."))
        
        # Schedule study sessions and life events
        today = datetime.now()
        scheduled_events = []
        
        # Determine schedule points
        study_start = today + timedelta(days=1)
        study_start = study_start.replace(hour=10, minute=0, second=0)
        
        for sub in subjects:
            # Event 1: Study block
            block_start = study_start.strftime("%Y-%m-%d %H:%M")
            block_end = (study_start + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            
            sched_args = {
                "title": f"{sub} Study Session",
                "start": block_start,
                "end": block_end,
                "description": f"Focused active study block on {sub} topics.",
                "category": "study"
            }
            steps.append(self.life_scheduler.log_tool_call("schedule_event", sched_args))
            sched_res = mcp_server.call_mcp_tool("schedule_event", sched_args)
            steps.append(self.life_scheduler.log_tool_response(sched_res))
            
            if sched_res.get("success"):
                scheduled_events.append(sched_res["event"])
                
            # Increment time for next day/block
            study_start += timedelta(days=1)
            
        if has_gym:
            gym_time = today + timedelta(days=1)
            gym_time = gym_time.replace(hour=18, minute=0, second=0)
            gym_args = {
                "title": "Gym Workout",
                "start": gym_time.strftime("%Y-%m-%d %H:%M"),
                "end": (gym_time + timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M"),
                "description": "Physical health balance - cardiorespiratory training.",
                "category": "life"
            }
            steps.append(self.life_scheduler.log_tool_call("schedule_event", gym_args))
            gym_res = mcp_server.call_mcp_tool("schedule_event", gym_args)
            steps.append(self.life_scheduler.log_tool_response(gym_res))
            
            if gym_res.get("success"):
                scheduled_events.append(gym_res["event"])
                
        state.variables["scheduled_events"] = scheduled_events
        steps.append(self.life_scheduler.log_output(
            f"Calendar integration complete. Balanced calendar created with {len(scheduled_events)} blocks scheduled safely."
        ))

        # ----------------------------------------------------
        # 6. END Node
        # ----------------------------------------------------
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "node_transition",
            "from_node": "LifeSchedulerAgent",
            "to_node": "END"
        })
        steps.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "type": "workflow_status",
            "message": "Workflow completed successfully. Final schedule written to database."
        })
        
        # Save final state data to return to client
        return {
            "status": "success",
            "steps": steps,
            "data": {
                "subjects": subjects,
                "optimized_tasks": optimized_tasks,
                "flashcards": flashcards_by_subject,
                "scheduled_events": scheduled_events
            }
        }
