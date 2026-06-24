import unittest
import os
import json
import shutil
import agents
import mcp_server
import cli_tool

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_OUTPUT_ICS = os.path.join(WORKSPACE_DIR, "test_output.ics")

class TestAstraFlowSystem(unittest.TestCase):
    
    def setUp(self):
        # Reset database for tests
        mcp_server.save_db([])
        
    def tearDown(self):
        # Clean up test output file
        if os.path.exists(TEST_OUTPUT_ICS):
            os.remove(TEST_OUTPUT_ICS)
            
    def test_multi_agent_workflow_simulation(self):
        """Verify the ADK multi-agent workflow generates expected steps and structured outputs."""
        prompt = "Chemistry Exam on Friday, gym at 6 PM. Prioritize my schedules."
        workflow = agents.AstraFlowWorkflow()
        result = workflow.run(prompt)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("steps", result)
        self.assertIn("data", result)
        
        # Verify agents executed in the workflow steps
        agents_logged = [step["agent"] for step in result["steps"] if "agent" in step]
        self.assertTrue(any("PlannerAgent" in a for a in agents_logged))
        self.assertTrue(any("TaskOptimizationAgent" in a for a in agents_logged))
        self.assertTrue(any("ExamStudyAgent" in a for a in agents_logged))
        self.assertTrue(any("LifeSchedulerAgent" in a for a in agents_logged))
        
        # Verify extracted variables
        data = result["data"]
        self.assertIn("Chemistry", data["subjects"])
        self.assertTrue(len(data["optimized_tasks"]) > 0)
        self.assertTrue(len(data["flashcards"]) > 0)
        self.assertTrue(len(data["scheduled_events"]) > 0)

    def test_mcp_schedule_tool(self):
        """Verify schedule_event MCP tool correctly validates dates, detects overlaps, and writes to database."""
        args = {
            "title": "Exam Study Block",
            "start": "2026-06-23 10:00",
            "end": "2026-06-23 12:00",
            "category": "study"
        }
        res = mcp_server.call_mcp_tool("schedule_event", args)
        self.assertTrue(res["success"])
        self.assertEqual(res["event"]["title"], "Exam Study Block")
        
        # Test conflict detection
        overlap_args = {
            "title": "Conflicting Exam Session",
            "start": "2026-06-23 11:00",
            "end": "2026-06-23 13:00",
            "category": "study"
        }
        res_conflict = mcp_server.call_mcp_tool("schedule_event", overlap_args)
        self.assertTrue(res_conflict["success"])
        self.assertIn("conflict detected", res_conflict["conflict_info"])

    def test_mcp_priority_tool(self):
        """Verify optimize_priority Eisenhower calculation logic."""
        args = {
            "tasks": [
                {"name": "Task A", "urgency": 5, "importance": 5},
                {"name": "Task B", "urgency": 2, "importance": 5},
                {"name": "Task C", "urgency": 1, "importance": 1}
            ]
        }
        res = mcp_server.call_mcp_tool("optimize_priority", args)
        self.assertTrue(res["success"])
        
        tasks = res["optimized_tasks"]
        self.assertEqual(tasks[0]["name"], "Task A")
        self.assertEqual(tasks[0]["quadrant"], "Do First (Quadrant I)")
        self.assertEqual(tasks[1]["name"], "Task B")
        self.assertEqual(tasks[1]["quadrant"], "Schedule (Quadrant II)")
        self.assertEqual(tasks[2]["name"], "Task C")
        self.assertEqual(tasks[2]["quadrant"], "Eliminate (Quadrant IV)")

    def test_security_safe_paths(self):
        """Verify directory traversal path bounds block files outside workspace."""
        # Inside workspace: must pass validation
        valid_path = os.path.join(WORKSPACE_DIR, "output.ics")
        safe_path = cli_tool.validate_safe_path(valid_path)
        self.assertEqual(safe_path, valid_path)
        
        # Outside workspace: must raise ValueError
        invalid_path = os.path.join(WORKSPACE_DIR, "..", "attacker_controlled.ics")
        with self.assertRaises(ValueError):
            cli_tool.validate_safe_path(invalid_path)
            
        # Invalid extension: must raise ValueError
        invalid_ext_path = os.path.join(WORKSPACE_DIR, "output.exe")
        with self.assertRaises(ValueError):
            cli_tool.validate_safe_path(invalid_ext_path)

    def test_cli_export_skill(self):
        """Verify CLI ICS exporter formats text and writes file correctly."""
        events = [
            {
                "title": "Chemistry Prep",
                "start": "2026-06-23 10:00",
                "end": "2026-06-23 12:00",
                "description": "Formulas",
                "category": "study"
            }
        ]
        events_str = json.dumps(events)
        
        # Run CLI export function directly
        cli_tool.export_ics(events_str, TEST_OUTPUT_ICS)
        self.assertTrue(os.path.exists(TEST_OUTPUT_ICS))
        
        with open(TEST_OUTPUT_ICS, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("BEGIN:VCALENDAR", content)
            self.assertIn("SUMMARY:Chemistry Prep", content)
            self.assertIn("DESCRIPTION:Formulas", content)
            self.assertIn("END:VCALENDAR", content)

if __name__ == "__main__":
    unittest.main()
