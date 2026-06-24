document.addEventListener("DOMContentLoaded", () => {
    // Current state caching
    let currentEvents = [];
    let activeWorkflowRunning = false;

    // --- Tab Navigation ---
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const currentTabTitle = document.getElementById("current-tab-title");
    const currentTabDesc = document.getElementById("current-tab-desc");

    const tabMeta = {
        "dashboard": {
            title: "AstraFlow Command Dashboard",
            desc: "High-fidelity multi-agent orchestration and local schedule synthesis."
        },
        "chat-agents": {
            title: "Multi-Agent Simulator Space",
            desc: "Observe the Planner, Optimizer, Study, and Life agents execute offline prompt tasks."
        },
        "calendar": {
            title: "Timeline Schedule Dashboard",
            desc: "Visual schedule maps and active recall card outputs compiled by the system."
        },
        "diagnostics": {
            title: "Security Shield Diagnostics",
            desc: "Verification metrics on workspace file boundaries and safe subprocess limits."
        }
    };

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            
            navItems.forEach(nav => nav.classList.remove("active"));
            tabPanes.forEach(pane => pane.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(`tab-${tabId}`).classList.add("active");
            
            // Update Headers
            if (tabMeta[tabId]) {
                currentTabTitle.textContent = tabMeta[tabId].title;
                currentTabDesc.textContent = tabMeta[tabId].desc;
            }
        });
    });

    // --- Sample Prompts ---
    const sampleBtns = document.querySelectorAll(".sample-prompt-btn");
    const chatInput = document.getElementById("chat-user-input");
    const chatForm = document.getElementById("chat-submit-form");

    sampleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            chatInput.value = btn.textContent;
            // Switch to chat tab
            document.querySelector('[data-tab="chat-agents"]').click();
            chatInput.focus();
        });
    });

    // --- Server Status Check ---
    const serverDbStatus = document.getElementById("server-db-status");
    const statsEventCount = document.getElementById("stats-event-count");

    async function checkServerStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            if (data.status === "online") {
                serverDbStatus.textContent = `DB: ${data.database.exists ? 'Persisted' : 'New'} | ${data.database.events_count} events`;
                statsEventCount.textContent = data.database.events_count;
            }
        } catch (err) {
            serverDbStatus.textContent = "Offline or unavailable";
        }
    }

    // Run status check periodically
    checkServerStatus();
    setInterval(checkServerStatus, 5000);

    // --- Clear Database ---
    const clearBtn = document.getElementById("clear-calendar-btn");
    clearBtn.addEventListener("click", async () => {
        if (confirm("Are you sure you want to clear the local calendar database?")) {
            try {
                const res = await fetch("/api/calendar/clear", { method: "POST" });
                const data = await res.json();
                if (data.status === "success") {
                    addLogEntry("System", "system", "Local database cleared by user request.");
                    checkServerStatus();
                    loadCalendarEvents();
                    renderFlashcards({});
                    alert("Database cleared successfully!");
                }
            } catch (err) {
                alert("Error clearing database.");
            }
        }
    });

    // --- Live Agent Graph Visualizer ---
    const graphNodes = {
        START: document.getElementById("node-START"),
        PlannerAgent: document.getElementById("node-PlannerAgent"),
        TaskOptimizationAgent: document.getElementById("node-TaskOptimizationAgent"),
        ExamStudyAgent: document.getElementById("node-ExamStudyAgent"),
        LifeSchedulerAgent: document.getElementById("node-LifeSchedulerAgent"),
        END: document.getElementById("node-END")
    };

    function resetGraphVisualizer() {
        Object.values(graphNodes).forEach(node => {
            if (node) {
                node.className = "graph-node node-idle";
            }
        });
    }

    function updateGraphNodeState(nodeName, stateClass) {
        const node = graphNodes[nodeName];
        if (node) {
            node.className = `graph-node ${stateClass}`;
        }
    }

    // --- Log Render Engine ---
    const logsContainer = document.getElementById("real-time-logs-container");
    const securityLogsContainer = document.getElementById("security-execution-logs");

    function addLogEntry(agent, type, message, details = null) {
        const entry = document.createElement("div");
        entry.className = `log-entry log-${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        let prefix = `[${timestamp}] [${agent}] `;
        
        if (type === "tool") {
            prefix += "🔧 MCP Tool Request: ";
        } else if (type === "tool-resp") {
            prefix += "📥 MCP Tool Output: ";
        } else if (type === "thought") {
            prefix += "💭 Reasoning Loop: ";
        } else if (type === "node_transition") {
            prefix += "⚡ Execution Path: ";
        }
        
        entry.textContent = prefix + message;

        // If JSON details exist, append a collapsible view
        if (details) {
            const collapse = document.createElement("div");
            collapse.className = "log-entry-collapsible";
            
            const header = document.createElement("div");
            header.className = "collapsible-header";
            header.innerHTML = `<span>View Payload Schema</span> <span>▼</span>`;
            
            const content = document.createElement("pre");
            content.className = "collapsible-content hidden";
            content.textContent = JSON.stringify(details, null, 2);
            
            header.addEventListener("click", () => {
                const isHidden = content.classList.contains("hidden");
                if (isHidden) {
                    content.classList.remove("hidden");
                    header.querySelector("span:last-child").textContent = "▲";
                } else {
                    content.classList.add("hidden");
                    header.querySelector("span:last-child").textContent = "▼";
                }
            });
            
            collapse.appendChild(header);
            collapse.appendChild(content);
            entry.appendChild(collapse);
        }
        
        logsContainer.appendChild(entry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
        
        // Parallel pipe to security logging for diagnostics tab
        if (type === "tool" || type === "tool-resp" || agent === "System") {
            const secEntry = document.createElement("div");
            secEntry.className = `log-entry log-${type}`;
            secEntry.textContent = `[Shield Monitor] ${prefix} ${message.substring(0, 100)}${message.length > 100 ? '...' : ''}`;
            securityLogsContainer.appendChild(secEntry);
            securityLogsContainer.scrollTop = securityLogsContainer.scrollHeight;
        }
    }

    // --- Chat Submissions & Workflow Playback ---
    const messagesContainer = document.getElementById("chat-messages-container");

    function addChatMessage(sender, content, role = "agent") {
        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${role} agent-${sender}`;
        
        const meta = document.createElement("div");
        meta.className = "bubble-meta";
        meta.innerHTML = `<strong>${sender}</strong> <small>${new Date().toLocaleTimeString()}</small>`;
        
        const body = document.createElement("div");
        body.className = "bubble-content";
        body.innerHTML = content.replace(/\n/g, "<br>");
        
        bubble.appendChild(meta);
        bubble.appendChild(body);
        messagesContainer.appendChild(bubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userPrompt = chatInput.value.trim();
        if (!userPrompt || activeWorkflowRunning) return;
        
        activeWorkflowRunning = true;
        chatInput.disabled = true;
        document.getElementById("chat-send-btn").disabled = true;
        
        // Reset Visualizers
        resetGraphVisualizer();
        logsContainer.innerHTML = "";
        
        // Add User Message
        addChatMessage("User", userPrompt, "user");
        addLogEntry("System", "system", `Launching offline ADK Multi-Agent pipeline for query: "${userPrompt}"`);
        chatInput.value = "";

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userPrompt })
            });
            const data = await res.json();
            
            if (data.status === "success") {
                // Playback simulation steps with delays to show agent transitions
                await playbackWorkflowSteps(data.steps);
                
                // Cache final results
                currentEvents = data.data.scheduled_events;
                
                // Refresh Calendar panel
                loadCalendarEvents();
                renderFlashcards(data.data.flashcards);
                checkServerStatus();
            } else {
                addLogEntry("System", "danger", `Workflow error: ${data.detail || 'Unknown error'}`);
                addChatMessage("System", "An error occurred executing the multi-agent simulator.");
            }
        } catch (err) {
            addLogEntry("System", "danger", `HTTP Connection error: ${err.message}`);
            addChatMessage("System", "Failed to connect to the backend server.");
        } finally {
            activeWorkflowRunning = false;
            chatInput.disabled = false;
            document.getElementById("chat-send-btn").disabled = false;
        }
    });

    // Playback steps dynamically
    async function playbackWorkflowSteps(steps) {
        let lastNode = null;
        
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            
            // Introduce a short visual delay to simulate thinking time
            await new Promise(resolve => setTimeout(resolve, 800));
            
            if (step.type === "workflow_status") {
                addLogEntry(step.agent, "system", step.message);
            } 
            else if (step.type === "node_transition") {
                addLogEntry("System", "node_transition", `Transitioning: ${step.from_node} ➔ ${step.to_node}`);
                
                // Update active visualization
                if (step.from_node && step.from_node !== "START") {
                    updateGraphNodeState(step.from_node, "node-completed");
                } else if (step.from_node === "START") {
                    updateGraphNodeState("START", "node-completed");
                }
                
                if (step.to_node && step.to_node !== "END") {
                    updateGraphNodeState(step.to_node, "node-running");
                } else if (step.to_node === "END") {
                    updateGraphNodeState("END", "node-completed");
                }
            } 
            else if (step.type === "thought") {
                addLogEntry(step.agent, "thought", step.message);
            } 
            else if (step.type === "tool_call") {
                addLogEntry(step.agent, "tool", `Invoked local MCP tool '${step.tool_name}'`, step.arguments);
            } 
            else if (step.type === "tool_response") {
                addLogEntry(step.agent, "tool-resp", `Received tool response status: ${step.response.success ? 'SUCCESS' : 'FAILED'}`, step.response);
            } 
            else if (step.type === "output") {
                addLogEntry(step.agent, "output", `Final Agent Output: ${step.message}`);
                addChatMessage(step.agent, step.message);
            }
        }
        
        // Ensure graph nodes are all marked completed
        Object.keys(graphNodes).forEach(node => {
            updateGraphNodeState(node, "node-completed");
        });
    }

    // --- Render Calendar Grid ---
    const calendarRows = document.getElementById("calendar-events-rows");

    async function loadCalendarEvents() {
        try {
            const res = await fetch("/api/calendar");
            const data = await res.json();
            if (data.status === "success") {
                currentEvents = data.events;
                renderCalendarRows(currentEvents);
            }
        } catch (err) {
            calendarRows.innerHTML = `<div class="empty-state text-danger">Failed to fetch calendar events from database.</div>`;
        }
    }

    function renderCalendarRows(events) {
        if (!events || events.length === 0) {
            calendarRows.innerHTML = `<div class="empty-state">No events scheduled. Run a chat request or create events.</div>`;
            return;
        }
        
        calendarRows.innerHTML = "";
        events.forEach(ev => {
            const row = document.createElement("div");
            row.className = "calendar-row";
            
            // Category Badge
            const catCol = document.createElement("div");
            catCol.className = "grid-col-label";
            const badge = document.createElement("span");
            badge.className = `cat-badge cat-${ev.category}`;
            badge.textContent = ev.category;
            catCol.appendChild(badge);
            
            // Title
            const titleCol = document.createElement("div");
            titleCol.innerHTML = `<strong>${ev.title}</strong>`;
            
            // Start
            const startCol = document.createElement("div");
            startCol.textContent = ev.start;
            
            // End
            const endCol = document.createElement("div");
            endCol.textContent = ev.end;
            
            // Description
            const descCol = document.createElement("div");
            descCol.className = "text-secondary small";
            descCol.textContent = ev.description || "-";
            
            row.appendChild(catCol);
            row.appendChild(titleCol);
            row.appendChild(startCol);
            row.appendChild(endCol);
            row.appendChild(descCol);
            
            calendarRows.appendChild(row);
        });
    }

    // --- Render Flashcards ---
    const flashcardsBox = document.getElementById("generated-flashcards-box");

    function renderFlashcards(flashcardsBySubject) {
        const allCards = [];
        Object.entries(flashcardsBySubject).forEach(([subject, cards]) => {
            cards.forEach(c => {
                allCards.push({ subject, ...c });
            });
        });
        
        if (allCards.length === 0) {
            flashcardsBox.innerHTML = `<div class="empty-state">No study cards generated yet. Run study workflow tasks.</div>`;
            return;
        }
        
        flashcardsBox.innerHTML = "";
        allCards.forEach(c => {
            const cardEl = document.createElement("div");
            cardEl.className = "flashcard-item";
            
            const front = document.createElement("div");
            front.className = "fc-front";
            front.innerHTML = `<span class="badge badge-purple" style="position:static; margin-right:6px;">${c.subject}</span> ${c.front}`;
            
            const back = document.createElement("div");
            back.className = "fc-back";
            back.textContent = c.back;
            
            cardEl.appendChild(front);
            cardEl.appendChild(back);
            
            flashcardsBox.appendChild(cardEl);
        });
    }

    // Load initial events on launch
    loadCalendarEvents();

    // --- Export Calendar ICS file (CLI Subprocess) ---
    const exportIcsBtn = document.getElementById("export-ics-btn");
    const exportSuccessBanner = document.getElementById("export-success-banner");
    const downloadIcsLink = document.getElementById("download-ics-link");

    exportIcsBtn.addEventListener("click", async () => {
        if (!currentEvents || currentEvents.length === 0) {
            alert("No events in current calendar schedule to export. Run a schedule workflow first!");
            return;
        }
        
        exportIcsBtn.disabled = true;
        exportIcsBtn.textContent = "Processing Subprocess...";
        
        try {
            const res = await fetch("/api/export", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    events: currentEvents,
                    filename: "weekly_schedule.ics"
                })
            });
            const data = await res.json();
            
            if (data.status === "success") {
                // Display download banner
                exportSuccessBanner.classList.remove("hidden");
                downloadIcsLink.href = `/api/download/${data.filename}`;
                downloadIcsLink.textContent = `Download ${data.filename} (${data.message.split("'")[1].split(/[\\/]/).pop()})`;
                
                // Log shield event
                const secEntry = document.createElement("div");
                secEntry.className = "log-entry log-tool-resp";
                secEntry.textContent = `[Shield Monitor] CLI Export verified. Output locked to: ${data.file_path}`;
                securityLogsContainer.appendChild(secEntry);
                
                alert("Subprocess ran successfully. Calendar ICS file generated within workspace bounds.");
            } else {
                alert(`Export failed: ${data.detail || 'Unknown error'}`);
            }
        } catch (err) {
            alert(`Error running CLI tool: ${err.message}`);
        } finally {
            exportIcsBtn.disabled = false;
            exportIcsBtn.textContent = "⇩ Export ICS File";
        }
    });
});
