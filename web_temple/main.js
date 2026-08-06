// Real-time variables
let config = {};
let isPartyRunning = false;
let statusInterval = null;
let isCensorActive = false;
let durationInterval = null;
let partyStartTime = null;
let restartAttempts = 0;
let lastStartTimestamp = null;

// Console log storage per tab
const logStreams = {
    "System": []
};
let activeTab = "System";

// HTML Elements
const serverSelect = document.getElementById("select-server");
const roomInput = document.getElementById("input-room-number");
const selectTempleBot = document.getElementById("select-temple-bot");
const btnStartParty = document.getElementById("btn-start-party");
const btnStopParty = document.getElementById("btn-stop-party");
const consoleTabsList = document.getElementById("console-tabs-list");
const consoleViewport = document.getElementById("console-viewport");
const chkAutoScroll = document.getElementById("chk-auto-scroll");
const btnClearLogs = document.getElementById("btn-clear-logs");

// Slots elements array
const slots = ["slot1", "slot2", "slot3", "slot4"];

// Setup event listeners once pywebview is ready
window.addEventListener("pywebviewready", () => {
    loadConfiguration();
    
    // Auto-save changes on config input edits
    document.querySelectorAll("input, select").forEach(elem => {
        elem.addEventListener("change", saveConfiguration);
    });

    // Setup username fields changes to update console tabs and enforce lowercase
    slots.forEach(slot => {
        const userEl = document.getElementById(`${slot}-username`);
        userEl.addEventListener("input", (e) => {
            e.target.value = e.target.value.toLowerCase();
            updateConsoleTabs();
        });
    });

    // Settings dropdown toggle
    const btnToggleSettings = document.getElementById("btn-toggle-settings");
    const settingsPanel = document.getElementById("settings-dropdown-panel");
    if (btnToggleSettings && settingsPanel) {
        btnToggleSettings.addEventListener("click", (e) => {
            e.stopPropagation();
            settingsPanel.classList.toggle("hidden");
        });
        document.addEventListener("click", (e) => {
            if (!settingsPanel.classList.contains("hidden") && !settingsPanel.contains(e.target)) {
                settingsPanel.classList.add("hidden");
            }
        });
    }

    // Password visibility toggle
    document.querySelectorAll(".btn-toggle-password").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = btn.previousElementSibling;
            if (input.type === "password") {
                input.type = "text";
                btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px; pointer-events: none;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
            } else {
                input.type = "password";
                btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px; pointer-events: none;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
            }
        });
    });

    const btnToggleCensor = document.getElementById("btn-toggle-censor");
    if (btnToggleCensor) {
        btnToggleCensor.addEventListener("click", () => {
            isCensorActive = !isCensorActive;
            const censorIcon = document.getElementById("censor-icon");
            if (isCensorActive) {
                document.body.classList.add("censor-active");
                btnToggleCensor.classList.add("active");
                censorIcon.innerHTML = `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>`;
            } else {
                document.body.classList.remove("censor-active");
                btnToggleCensor.classList.remove("active");
                censorIcon.innerHTML = `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>`;
            }
            updateConsoleTabs();
            if (isPartyRunning) {
                toggleCredentialsVisibility(true);
            }
        });
    }

    btnStartParty.addEventListener("click", startParty);
    btnStopParty.addEventListener("click", stopParty);

    const btnResetConfig = document.getElementById("btn-reset-config");
    if (btnResetConfig) {
        btnResetConfig.addEventListener("click", () => {
            if (confirm("Are you sure you want to reset all slot configurations to defaults?")) {
                window.pywebview.api.reset_config().then(loadedConfig => {
                    // Preserve current usernames and passwords in the UI
                    slots.forEach(slot => {
                        const currentUsername = document.getElementById(`${slot}-username`).value;
                        const currentPassword = document.getElementById(`${slot}-password`).value;
                        if (loadedConfig.slots[slot]) {
                            loadedConfig.slots[slot].username = currentUsername;
                            loadedConfig.slots[slot].password = currentPassword;
                        }
                    });
                    
                    config = loadedConfig;
                    
                    serverSelect.value = config.server || "Alteon";
                    roomInput.value = config.room_number || 9099;
                    selectTempleBot.value = config.temple_bot_type || "MidnightSunBot";
                    
                    slots.forEach(slot => {
                        const slotConfig = config.slots[slot] || {};
                        document.getElementById(`${slot}-class`).value = slotConfig.char_class || "";
                    });
                    
                    saveConfiguration();
                    updateConsoleTabs();
                    checkActiveBotStatuses();
                });
            }
        });
    }
});

// Load Config from Python API
function loadConfiguration() {
    window.pywebview.api.load_config().then(loadedConfig => {
        config = loadedConfig;
        
        serverSelect.value = config.server || "Alteon";
        roomInput.value = config.room_number || 9099;
        selectTempleBot.value = config.temple_bot_type || "MidnightSunBot";
        
        // Load auto-restart settings
        document.getElementById("chk-auto-restart").checked = !!config.auto_restart_enabled;
        document.getElementById("input-restart-delay").value = config.auto_restart_delay !== undefined ? config.auto_restart_delay : 30;
        document.getElementById("input-restart-max-attempts").value = config.auto_restart_max_attempts !== undefined ? config.auto_restart_max_attempts : 3;
        
        slots.forEach(slot => {
            const slotConfig = config.slots[slot] || {};
            
            document.getElementById(`${slot}-username`).value = slotConfig.username || "";
            document.getElementById(`${slot}-password`).value = slotConfig.password || "";
            document.getElementById(`${slot}-class`).value = slotConfig.char_class || "";
            document.getElementById(`${slot}-is-taunter`).checked = !!slotConfig.is_taunter;
        });
        
        updateConsoleTabs();
        checkActiveBotStatuses();
    });
}

// Gather GUI UI inputs and post to Save
function saveConfiguration() {
    if (isPartyRunning) return; // Prevent edits when running
    
    config.server = serverSelect.value;
    config.room_number = parseInt(roomInput.value) || 9099;
    config.temple_bot_type = selectTempleBot.value;
    
    config.auto_restart_enabled = document.getElementById("chk-auto-restart").checked;
    config.auto_restart_delay = parseInt(document.getElementById("input-restart-delay").value) || 30;
    config.auto_restart_max_attempts = parseInt(document.getElementById("input-restart-max-attempts").value) || 3;
    
    slots.forEach(slot => {
        config.slots[slot] = {
            username: document.getElementById(`${slot}-username`).value.trim(),
            password: document.getElementById(`${slot}-password`).value.trim(),
            char_class: document.getElementById(`${slot}-class`).value.trim(),
            is_taunter: document.getElementById(`${slot}-is-taunter`).checked
        };
    });

    window.pywebview.api.save_config(config);
}

// Dynamic Tab Updating
function updateConsoleTabs() {
    // Keep reference to currently selected tab
    const currentTab = activeTab;
    
    // Clear tabs list except System
    consoleTabsList.innerHTML = `<button class="console-tab ${activeTab === 'System' ? 'active' : ''}" data-source="System">System</button>`;
    
    slots.forEach((slot, index) => {
        const usernameVal = document.getElementById(`${slot}-username`).value.trim();
        const tabLabel = isCensorActive ? `Player ${index + 1}` : (usernameVal || `Slot ${index + 1}`);
        const tabId = usernameVal || slot;
        
        // Ensure stream array exists
        if (!logStreams[tabId]) {
            logStreams[tabId] = [];
        }
        
        const activeClass = activeTab === tabId ? "active" : "";
        consoleTabsList.innerHTML += `<button class="console-tab ${activeClass}" data-source="${tabId}">${tabLabel}</button>`;
    });

    // Rebind clicking handlers
    document.querySelectorAll(".console-tab").forEach(tab => {
        tab.addEventListener("click", (e) => {
            document.querySelectorAll(".console-tab").forEach(t => t.classList.remove("active"));
            e.target.classList.add("active");
            activeTab = e.target.getAttribute("data-source");
            renderActiveLogs();
        });
    });
}

// Start Party
function startParty(isAuto = false) {
    saveConfiguration();
    
    if (isAuto !== true) {
        restartAttempts = 0;
        partyStartTime = Date.now();
    }
    btnStartParty.disabled = true;
    
    window.pywebview.api.start_party(config).then(res => {
        if (res.success) {
            isPartyRunning = true;
            lastStartTimestamp = Date.now();
            btnStartParty.classList.add("hidden");
            btnStopParty.classList.remove("hidden");
            btnStartParty.disabled = false;
            
            // Start duration counter
            const durationCounter = document.getElementById("duration-counter");
            const durationVal = document.getElementById("duration-val");
            if (durationCounter) durationCounter.classList.remove("hidden");
            if (durationInterval) clearInterval(durationInterval);
            durationInterval = setInterval(() => {
                const diff = Date.now() - partyStartTime;
                const hrs = String(Math.floor(diff / 3600000)).padStart(2, '0');
                const mins = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0');
                const secs = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
                if (durationVal) durationVal.innerText = `${hrs}:${mins}:${secs}`;
            }, 1000);
            
            // Hide reset config button inside popover
            const btnReset = document.getElementById("btn-reset-config");
            if (btnReset) btnReset.classList.add("hidden");
            
            // Lock fields
            toggleFormFieldsLock(true);
            
            // Hide credentials and show summary
            toggleCredentialsVisibility(true);
            
            // Start Polling Status
            startTelemetryPolling();
        } else {
            alert(res.error || "Failed to start party.");
            btnStartParty.disabled = false;
        }
    });
}

// Stop Party
function stopParty() {
    btnStopParty.disabled = true;
    
    // Clear any active auto-restart timers
    restartTimerActive = false;
    restartTimerTarget = null;
    isStoppingForRestart = false;
    updateRestartStatusText("");
    
    window.pywebview.api.stop_party().then(() => {
        isPartyRunning = false;
        btnStopParty.classList.add("hidden");
        btnStartParty.removeAttribute("disabled");
        btnStartParty.classList.remove("hidden");
        btnStopParty.disabled = false;
        
        // Stop and reset duration counter
        if (durationInterval) {
            clearInterval(durationInterval);
            durationInterval = null;
        }
        const durationCounter = document.getElementById("duration-counter");
        if (durationCounter) durationCounter.classList.add("hidden");
        
        // Show reset config button inside popover
        const btnReset = document.getElementById("btn-reset-config");
        if (btnReset) btnReset.classList.remove("hidden");
        
        // Unlock fields
        toggleFormFieldsLock(false);
        
        // Show credentials input again
        toggleCredentialsVisibility(false);
        
        // Stop Polling Status
        stopTelemetryPolling();
        
        // Clean layouts back to offline defaults
        slots.forEach(slot => {
            const badge = document.getElementById(`badge-${slot}`);
            if (badge) {
                badge.className = "status-badge";
                badge.innerText = "Offline";
            }
            const tel = document.getElementById(`telemetry-${slot}`);
            if (tel) {
                tel.classList.add("hidden");
            }
        });
    });
}

function startTelemetryPolling() {
    stopTelemetryPolling();
    checkActiveBotStatuses();
    statusInterval = setInterval(checkActiveBotStatuses, 1000);
}

function stopTelemetryPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
}

function checkActiveBotStatuses() {
    window.pywebview.api.get_status().then(statuses => {
        slots.forEach(slot => {
            const status = statuses[slot];
            const badge = document.getElementById(`badge-${slot}`);
            const telemetryPanel = document.getElementById(`telemetry-${slot}`);
            
            if (status && status.running) {
                // Online
                badge.innerText = status.is_connected ? "Online" : "Connecting...";
                badge.className = "status-badge online";
                
                // Show telemetry
                telemetryPanel.classList.remove("hidden");
                
                // Map details
                document.getElementById(`tel-${slot}-map`).innerText = status.map || "-";
                document.getElementById(`tel-${slot}-cell`).innerText = `${status.cell} (${status.pad})` || "-";
                
                // HP
                const hpPercent = status.max_hp > 0 ? (status.hp / status.max_hp) * 100 : 0;
                document.getElementById(`val-${slot}-hp`).innerText = `${status.hp}/${status.max_hp}`;
                document.getElementById(`bar-${slot}-hp`).style.width = `${hpPercent}%`;
                
                // MP
                const mpPercent = status.max_mp > 0 ? (status.mp / status.max_mp) * 100 : 0;
                document.getElementById(`val-${slot}-mp`).innerText = `${status.mp}/${status.max_mp}`;
                document.getElementById(`bar-${slot}-mp`).style.width = `${mpPercent}%`;
                
                if (status.is_dead) {
                    badge.innerText = "DEAD";
                    badge.className = "status-badge dead";
                }
            } else {
                // Offline
                badge.className = "status-badge";
                badge.innerText = "Offline";
                telemetryPanel.classList.add("hidden");
            }
        });

        // Monitor client connections and auto-restart if dc is detected
        handleDisconnectMonitoring(statuses);
    });
}

// Appending Logs into console streams
window.addSlaveLog = function(username, htmlMsg) {
    // If username is not System, check if it maps to any slot username
    let targetStream = "System";
    if (username !== "System") {
        slots.forEach(slot => {
            const slotUsername = document.getElementById(`${slot}-username`).value.trim();
            if (slotUsername && slotUsername.toLowerCase() === username.toLowerCase()) {
                targetStream = slotUsername;
            }
        });
    }

    if (!logStreams[targetStream]) {
        logStreams[targetStream] = [];
    }
    
    // Append to array
    logStreams[targetStream].push(htmlMsg);
    
    // Cap log lines to 200 to save memory
    if (logStreams[targetStream].length > 200) {
        logStreams[targetStream].shift();
    }
    
    // Render immediately if it is active tab
    if (activeTab === targetStream) {
        const line = document.createElement("div");
        line.className = "log-line";
        line.innerHTML = htmlMsg;
        consoleViewport.appendChild(line);
        
        if (chkAutoScroll && chkAutoScroll.checked) {
            consoleViewport.scrollTop = consoleViewport.scrollHeight;
        }
    }
};

function renderActiveLogs() {
    consoleViewport.innerHTML = "";
    const stream = logStreams[activeTab] || [];
    stream.forEach(htmlMsg => {
        const line = document.createElement("div");
        line.className = "log-line";
        line.innerHTML = htmlMsg;
        consoleViewport.appendChild(line);
    });
    
    if (chkAutoScroll && chkAutoScroll.checked) {
        consoleViewport.scrollTop = consoleViewport.scrollHeight;
    }
}

function clearLogs() {
    logStreams[activeTab] = [];
    consoleViewport.innerHTML = "";
}

function toggleFormFieldsLock(isLocked) {
    serverSelect.disabled = isLocked;
    roomInput.disabled = isLocked;
    selectTempleBot.disabled = isLocked;
    
    slots.forEach(slot => {
        document.getElementById(`${slot}-username`).disabled = isLocked;
        document.getElementById(`${slot}-password`).disabled = isLocked;
        document.getElementById(`${slot}-class`).disabled = isLocked;
        document.getElementById(`${slot}-is-taunter`).disabled = isLocked;
    });
}

// Censor Mode Credentials toggler on party start
function toggleCredentialsVisibility(showInfoDisplay) {
    slots.forEach((slot, index) => {
        const usernameFg = document.getElementById(`${slot}-username`).closest('.form-group');
        const passwordFg = document.getElementById(`${slot}-password`).closest('.form-group');
        const usernameInput = document.getElementById(`${slot}-username`);
        
        if (showInfoDisplay) {
            usernameFg.classList.add('hidden');
            passwordFg.classList.add('hidden');
            
            const displayVal = isCensorActive ? `Player ${index + 1}` : (usernameInput.value || '-');
            
            let summaryEl = document.getElementById(`${slot}-summary-display`);
            if (!summaryEl) {
                summaryEl = document.createElement('div');
                summaryEl.id = `${slot}-summary-display`;
                summaryEl.className = 'form-group account-summary-display';
                summaryEl.innerHTML = `
                    <label>Active Account</label>
                    <div style="font-weight: 600; color: #fff; background-color: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-color); height: 38px; display: flex; align-items: center; font-size: 0.85rem;">
                        ${displayVal}
                    </div>
                `;
                const classFg = document.getElementById(`${slot}-class`).closest('.form-group');
                classFg.parentNode.insertBefore(summaryEl, classFg);
            } else {
                summaryEl.querySelector('div').innerText = displayVal;
                summaryEl.classList.remove('hidden');
            }
        } else {
            usernameFg.classList.remove('hidden');
            passwordFg.classList.remove('hidden');
            
            const summaryEl = document.getElementById(`${slot}-summary-display`);
            if (summaryEl) {
                summaryEl.classList.add('hidden');
            }
        }
    });
}

let isStoppingForRestart = false;
let restartTimerActive = false;
let restartTimerTarget = null;

function updateRestartStatusText(text) {
    const ind = document.getElementById("restart-status-indicator");
    if (ind) ind.innerText = text;
}

function handleDisconnectMonitoring(statuses) {
    if (!config.auto_restart_enabled) {
        isStoppingForRestart = false;
        restartTimerActive = false;
        restartTimerTarget = null;
        updateRestartStatusText("");
        return;
    }
    
    // If the restart timer is active (waiting for delay to start), handle the countdown
    if (restartTimerActive) {
        const remainingMs = restartTimerTarget - Date.now();
        const remainingSecs = Math.max(0, Math.ceil(remainingMs / 1000));
        
        updateRestartStatusText(`Auto-Restarting in ${remainingSecs}s...`);
        
        if (remainingMs <= 0) {
            restartTimerActive = false;
            restartTimerTarget = null;
            updateRestartStatusText("Auto-Restarting now!");
            
            restartAttempts++;
            const maxAttempts = parseInt(config.auto_restart_max_attempts) || 3;
            addSlaveLog("System", `<span class="log-yellow log-bold">[System] Restarting party bots (Attempt ${restartAttempts}/${maxAttempts})...</span>`);
            
            setTimeout(() => {
                updateRestartStatusText("");
                startParty(true);
            }, 1000);
        }
        return;
    }

    if (isStoppingForRestart) return;
    
    // Check if we are still within the grace period (45 seconds) to allow login
    if (lastStartTimestamp && (Date.now() - lastStartTimestamp < 45000)) {
        updateRestartStatusText("");
        return;
    }
    
    // Otherwise, check if there is an active disconnect
    let hasDisconnect = false;
    slots.forEach(slot => {
        const usernameVal = document.getElementById(`${slot}-username`).value.trim();
        if (usernameVal) {
            const status = statuses[slot];
            if (status && status.running && !status.is_connected) {
                hasDisconnect = true;
            }
        }
    });
    
    if (hasDisconnect) {
        const maxAttempts = parseInt(config.auto_restart_max_attempts) || 3;
        if (restartAttempts >= maxAttempts) {
            updateRestartStatusText("Auto-restart limit reached!");
            addSlaveLog("System", `<span class="log-red log-bold">[System] Error: Auto-restart failed after ${maxAttempts} attempts. Stopping bots completely.</span>`);
            
            isStoppingForRestart = true;
            window.pywebview.api.stop_party().then(() => {
                isPartyRunning = false;
                isStoppingForRestart = false;
                btnStopParty.classList.add("hidden");
                btnStartParty.removeAttribute("disabled");
                btnStartParty.classList.remove("hidden");
                btnStopParty.disabled = false;
                
                const btnReset = document.getElementById("btn-reset-config");
                if (btnReset) btnReset.classList.remove("hidden");
                
                toggleFormFieldsLock(false);
                toggleCredentialsVisibility(false);
                stopTelemetryPolling();
            });
            return;
        }

        // Trigger immediate stop and start restart timer
        isStoppingForRestart = true;
        updateRestartStatusText("Stopping all bots...");
        addSlaveLog("System", `<span class="log-red log-bold">[System] Disconnect detected. Stopping all clients immediately...</span>`);
        
        window.pywebview.api.stop_party().then(() => {
            isPartyRunning = false;
            isStoppingForRestart = false;
            btnStopParty.classList.add("hidden");
            btnStartParty.removeAttribute("disabled");
            btnStartParty.classList.remove("hidden");
            btnStopParty.disabled = false;
            
            const btnReset = document.getElementById("btn-reset-config");
            if (btnReset) btnReset.classList.remove("hidden");
            
            toggleFormFieldsLock(false);
            toggleCredentialsVisibility(false);
            stopTelemetryPolling();
            
            const delaySecs = parseInt(config.auto_restart_delay) || 30;
            restartTimerActive = true;
            restartTimerTarget = Date.now() + (delaySecs * 1000);
            
            // Re-start status polling loop to update the countdown
            startTelemetryPolling();
        });
    }
}

// Info bubble click toggle handler
document.addEventListener("DOMContentLoaded", () => {
    const titleClick = document.getElementById("app-title-click");
    const infoBubble = document.getElementById("info-bubble");
    if (titleClick && infoBubble) {
        titleClick.addEventListener("click", (e) => {
            e.stopPropagation();
            infoBubble.classList.toggle("show");
        });
        document.addEventListener("click", () => {
            infoBubble.classList.remove("show");
        });
        infoBubble.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }
});
