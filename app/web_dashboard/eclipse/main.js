// Real-time variables
let config = {};
let isPartyRunning = false;
let statusInterval = null;
let isCensorActive = false;
let durationInterval = null;
let partyStartTime = null;
let restartAttempts = 0;
let lastStartTimestamp = null;

const SLOT_HARDCODED_SETTINGS = {
    slot1: { converge_type: "sun", taunt_parity: "odd" },
    slot2: { converge_type: "sun", taunt_parity: "even" },
    slot3: { converge_type: "moon", taunt_parity: "odd" },
    slot4: { converge_type: "moon", taunt_parity: "even" }
};

const isEmbedded = window.parent && window.parent !== window;

// Global Theme Manager
function applyTheme(themeName) {
    if (isEmbedded) return;
    document.body.classList.remove("theme-red", "theme-pink", "theme-blue", "theme-green");
    if (themeName !== "default") {
        document.body.classList.add(`theme-${themeName}`);
    }
    if (config) {
        config.theme = themeName;
    }
}

function updateActiveThemeDot(theme) {
    document.querySelectorAll(".theme-dot").forEach(dot => {
        if (dot.getAttribute("data-theme") === theme) {
            dot.classList.add("active");
        } else {
            dot.classList.remove("active");
        }
    });
}



// Console log storage per tab
const logStreams = {
    "System": []
};
let activeTab = "System";

// HTML Elements
const serverSelect = document.getElementById("select-server");
const roomInput = {
    get value() { return "99999"; },
    set value(val) {},
    disabled: false
};
const btnStartParty = document.getElementById("btn-start-party");
const btnStopParty = document.getElementById("btn-stop-party");
const consoleTabsList = document.getElementById("console-tabs-list");
const consoleViewport = document.getElementById("console-viewport");
const chkAutoScroll = document.getElementById("chk-auto-scroll");
const btnClearLogs = document.getElementById("btn-clear-logs");

// Slots elements array
const slots = ["slot1", "slot2", "slot3", "slot4"];

    function initApp() {
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
        btnClearLogs.addEventListener("click", clearLogs);

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
                        
                        slots.forEach(slot => {
                            const slotConfig = config.slots[slot] || {};
                            document.getElementById(`${slot}-class`).value = slotConfig.char_class || "";
                            document.getElementById(`${slot}-light-gather`).checked = !!slotConfig.light_gather_taunter;
                            
                            if (slot === "slot3") {
                                document.getElementById("slot3-moon-haze").checked = !!slotConfig.moon_haze_taunter;
                            }
                            if (slot === "slot4") {
                                document.getElementById("slot4-sunset-knight").checked = !!slotConfig.sunset_knight_taunter;
                            }
                        });
                        
                        saveConfiguration();
                        updateConsoleTabs();
                        checkActiveBotStatuses();
                    });
                }
            });
        }
    }

    if (window.pywebview && window.pywebview.api) {
        initApp();
    } else {
        window.addEventListener("pywebviewready", initApp);
    }

// Load Config from Python API
function loadConfiguration() {
    window.pywebview.api.load_config().then(loadedConfig => {
        config = loadedConfig;
        
        serverSelect.value = config.server || "Alteon";
        roomInput.value = config.room_number || 9099;
        
        // Load auto-restart settings
        document.getElementById("chk-auto-restart").checked = !!config.auto_restart_enabled;
        document.getElementById("input-restart-delay").value = config.auto_restart_delay !== undefined ? config.auto_restart_delay : 30;
        document.getElementById("input-restart-max-attempts").value = config.auto_restart_max_attempts !== undefined ? config.auto_restart_max_attempts : 3;
        
        slots.forEach(slot => {
            const slotConfig = config.slots[slot] || {};
            
            document.getElementById(`${slot}-username`).value = slotConfig.username || "";
            document.getElementById(`${slot}-password`).value = slotConfig.password || "";
            document.getElementById(`${slot}-class`).value = slotConfig.char_class || "";
            document.getElementById(`${slot}-light-gather`).checked = !!slotConfig.light_gather_taunter;
            
            if (slot === "slot3") {
                document.getElementById("slot3-moon-haze").checked = !!slotConfig.moon_haze_taunter;
            }
            if (slot === "slot4") {
                document.getElementById("slot4-sunset-knight").checked = !!slotConfig.sunset_knight_taunter;
            }
        });
        
        if (!isEmbedded) {
            const savedTheme = config.theme || "default";
            updateActiveThemeDot(savedTheme);
            applyTheme(savedTheme);
        } else {
            const selectorGroup = document.getElementById("theme-selector-group");
            if (selectorGroup) {
                const parentGroup = selectorGroup.closest(".form-group-inline");
                if (parentGroup) parentGroup.style.display = "none";
            }
        }
        
        updateConsoleTabs();
        checkActiveBotStatuses();
    });
}

// Gather GUI UI inputs and post to Save
function saveConfiguration() {
    if (isPartyRunning) return; // Prevent edits when running
    
    config.server = serverSelect.value;
    config.room_number = parseInt(roomInput.value) || 9099;
    
    config.auto_restart_enabled = document.getElementById("chk-auto-restart").checked;
    config.auto_restart_delay = parseInt(document.getElementById("input-restart-delay").value) || 30;
    config.auto_restart_max_attempts = parseInt(document.getElementById("input-restart-max-attempts").value) || 3;
    if (!isEmbedded) {
        const activeThemeDot = document.querySelector(".theme-dot.active");
        config.theme = activeThemeDot ? activeThemeDot.getAttribute("data-theme") : "default";
    }
    
    slots.forEach(slot => {
        config.slots[slot] = {
            username: document.getElementById(`${slot}-username`).value.trim(),
            password: document.getElementById(`${slot}-password`).value.trim(),
            char_class: document.getElementById(`${slot}-class`).value.trim(),
            converge_type: SLOT_HARDCODED_SETTINGS[slot].converge_type,
            taunt_parity: SLOT_HARDCODED_SETTINGS[slot].taunt_parity,
            light_gather_taunter: document.getElementById(`${slot}-light-gather`).checked
        };
        
        if (slot === "slot3") {
            config.slots.slot3.moon_haze_taunter = document.getElementById("slot3-moon-haze").checked;
        }
        if (slot === "slot4") {
            config.slots.slot4.sunset_knight_taunter = document.getElementById("slot4-sunset-knight").checked;
        }
    });

    window.pywebview.api.save_config(config);
}

// Dynamic Tab Updating
function updateConsoleTabs() {
    // Keep reference to currently selected tab
    const previousActive = activeTab;
    
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
            
            // Hide reset button
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
        const durationVal = document.getElementById("duration-val");
        if (durationCounter) durationCounter.classList.add("hidden");
        if (durationVal) durationVal.innerText = "00:00:00";
        
        // Show reset button
        const btnReset = document.getElementById("btn-reset-config");
        if (btnReset) btnReset.classList.remove("hidden");
        
        // Unlock fields
        toggleFormFieldsLock(false);
        
        // Show credentials and hide summary
        toggleCredentialsVisibility(false);
        
        // Stop Polling Status
        stopTelemetryPolling();
        
        // Clean layouts
        slots.forEach(slot => {
            document.getElementById(`badge-${slot}`).className = "status-badge";
            document.getElementById(`badge-${slot}`).innerText = "Offline";
            document.getElementById(`telemetry-${slot}`).classList.add("hidden");
        });
    });
}

// Lock/Unlock input controls
function toggleFormFieldsLock(lock) {
    document.querySelectorAll("input, select").forEach(elem => {
        if (elem.id !== "chk-auto-scroll") {
            elem.disabled = lock;
        }
    });
}

// Status telemetry polling
function startTelemetryPolling() {
    if (statusInterval) clearInterval(statusInterval);
    
    // Initial call
    checkActiveBotStatuses();
    
    // Poll every 1 second
    statusInterval = setInterval(checkActiveBotStatuses, 1000);
}

function stopTelemetryPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
}

function formatHP(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(2) + "M";
    } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + "K";
    }
    return value;
}

function checkActiveBotStatuses() {
    window.pywebview.api.get_status().then(data => {
        const statuses = data.statuses || data;
        const monsters = data.monsters || [];
        const systemStats = data.system_stats || null;

        // Sync running state from Python backend
        let anySlotRunning = false;
        slots.forEach(slot => {
            const status = statuses[slot];
            if (status && status.running) {
                anySlotRunning = true;
            }
        });
        
        if (anySlotRunning && !isPartyRunning) {
            isPartyRunning = true;
            btnStartParty.classList.add("hidden");
            btnStopParty.classList.remove("hidden");
            toggleFormFieldsLock(true);
            toggleCredentialsVisibility(true);
            
            const btnReset = document.getElementById("btn-reset-config");
            if (btnReset) btnReset.classList.add("hidden");
            
            const durationCounter = document.getElementById("duration-counter");
            if (durationCounter) durationCounter.classList.remove("hidden");
        }
        
        const timeRunningSecs = data._time_running || statuses._time_running;
        if (isPartyRunning && timeRunningSecs !== undefined) {
            partyStartTime = Date.now() - (timeRunningSecs * 1000);
            if (!durationInterval) {
                const durationVal = document.getElementById("duration-val");
                durationInterval = setInterval(() => {
                    const diff = Date.now() - partyStartTime;
                    const hrs = String(Math.floor(diff / 3600000)).padStart(2, '0');
                    const mins = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0');
                    const secs = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
                    if (durationVal) durationVal.innerText = `${hrs}:${mins}:${secs}`;
                }, 1000);
            }
        }

        // Process CPU/Mem telemetry in header
        if (systemStats) {
            const cpuEl = document.getElementById("sys-cpu");
            const memEl = document.getElementById("sys-mem");
            if (cpuEl) cpuEl.innerText = `${systemStats.cpu}%`;
            if (memEl) memEl.innerText = `${systemStats.memory} MB`;
        }

        // Process Monsters HP Panel
        const monstersPanel = document.getElementById("monsters-panel");
        const monstersList = document.getElementById("monsters-list");
        if (monstersPanel && monstersList) {
            if (monsters.length > 0) {
                monstersPanel.classList.remove("hidden");
                monstersList.innerHTML = monsters.map(mon => {
                    const hpPercent = mon.max_hp > 0 ? ((mon.hp / mon.max_hp) * 100).toFixed(1) : 0;
                    const formattedHp = mon.hp.toLocaleString();
                    const formattedMaxHp = mon.max_hp.toLocaleString();
                    return `
                        <div class="monster-hp-card">
                            <div class="monster-info-row">
                                <span class="monster-name">${mon.name}</span>
                                <span class="monster-hp-text">${formattedHp} / ${formattedMaxHp} (${hpPercent}%)</span>
                            </div>
                            <div class="monster-hp-bar-bg">
                                <div class="monster-hp-bar-fill" style="width: ${hpPercent}%"></div>
                            </div>
                        </div>
                    `;
                }).join("");
            } else {
                monstersPanel.classList.add("hidden");
                monstersList.innerHTML = "";
            }
        }

        slots.forEach(slot => {
            const status = statuses[slot];
            const badge = document.getElementById(`badge-${slot}`);
            const telemetryPanel = document.getElementById(`telemetry-${slot}`);
            const card = document.getElementById(`card-${slot}`);
            const soeInfoEl = document.getElementById(`${slot}-info-soe`);
            const cooldownsEl = document.getElementById(`cooldowns-${slot}`);
            
            // Clean active outlines
            if (card) {
                card.classList.remove("taunt-active-highlight");
                card.classList.remove("taunt-error-highlight");
            }
            
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
                
                // SoE indicator in running info display
                if (soeInfoEl) {
                    const qty = status.scroll_enrage_qty !== undefined ? status.scroll_enrage_qty : 0;
                    soeInfoEl.innerText = qty;
                    
                    // Style by quantity
                    if (qty >= 10) {
                        soeInfoEl.style.color = "#10b981"; // Green
                    } else if (qty > 0) {
                        soeInfoEl.style.color = "#f59e0b"; // Orange
                    } else {
                        soeInfoEl.style.color = "#ef4444"; // Red
                    }
                }
                
                // Error outlines
                if (card && status.taunt_error) {
                    card.classList.add("taunt-error-highlight");
                }
                
                // Cooldowns
                if (cooldownsEl && status.cooldowns) {
                    cooldownsEl.innerHTML = "";
                    for (let i = 0; i <= 5; i++) {
                        const cd = status.cooldowns[i] || 0.0;
                        const label = i === 0 ? "AA" : i;
                        const badgeClass = i === 5 ? "skill-cd-badge skill-5-badge" : "skill-cd-badge";
                        
                        if (cd > 0) {
                            cooldownsEl.innerHTML += `
                                <div class="${badgeClass} on-cooldown">
                                    <span class="skill-idx">${label}</span>
                                    <span class="skill-cd-val">${cd}s</span>
                                </div>
                            `;
                        } else {
                            cooldownsEl.innerHTML += `
                                <div class="${badgeClass} ready">
                                    <span class="skill-idx">${label}</span>
                                    <span class="skill-cd-val">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                    </span>
                                </div>
                            `;
                        }
                    }
                }
            } else {
                // Offline
                badge.className = "status-badge";
                badge.innerText = "Offline";
                telemetryPanel.classList.add("hidden");
                if (soeInfoEl) {
                    soeInfoEl.innerText = "0";
                    soeInfoEl.style.color = "#ef4444";
                }
            }
        });

        // Monitor client connections and auto-restart if dc is detected
        handleDisconnectMonitoring(statuses);
    });
}

// Add logs from Python redirector stream
window.addSlaveLog = function(username, htmlMsg) {
    // Determine mapping target tab
    let targetTab = "System";
    if (username !== "System") {
        // Resolve if we match any slot's active username input
        slots.forEach(slot => {
            const inputVal = document.getElementById(`${slot}-username`).value.trim();
            if (inputVal && inputVal.toLowerCase() === username.toLowerCase()) {
                targetTab = inputVal;
            }
        });
    }

    if (!logStreams[targetTab]) {
        logStreams[targetTab] = [];
    }
    
    // Store in stream (limit log buffer size to 500 lines)
    logStreams[targetTab].push(htmlMsg);
    if (logStreams[targetTab].length > 500) {
        logStreams[targetTab].shift();
    }
    
    // If target tab is active, append to viewport in real-time
    if (activeTab === targetTab) {
        const line = document.createElement("div");
        line.className = "log-line";
        line.innerHTML = htmlMsg;
        consoleViewport.appendChild(line);
        
        // Auto scroll
        if (chkAutoScroll.checked) {
            consoleViewport.scrollTop = consoleViewport.scrollHeight;
        }
    }
};

// Render whole log buffer on tab click
function renderActiveLogs() {
    consoleViewport.innerHTML = "";
    const activeStream = logStreams[activeTab] || [];
    
    activeStream.forEach(htmlMsg => {
        const line = document.createElement("div");
        line.className = "log-line";
        line.innerHTML = htmlMsg;
        consoleViewport.appendChild(line);
    });
    
    if (chkAutoScroll.checked) {
        consoleViewport.scrollTop = consoleViewport.scrollHeight;
    }
}

// Clear log buffers
function clearLogs() {
    logStreams[activeTab] = [];
    consoleViewport.innerHTML = "";
}

// Toggle inputs fields and show running display
function toggleCredentialsVisibility(showInfoDisplay) {
    slots.forEach((slot, index) => {
        const inputsContainer = document.getElementById(`${slot}-inputs-container`);
        const runningDisplay = document.getElementById(`${slot}-running-display`);
        
        if (!inputsContainer || !runningDisplay) return;
        
        if (showInfoDisplay) {
            // Hide editable inputs container
            inputsContainer.classList.add("hidden");
            
            // Populate running display info
            const usernameInput = document.getElementById(`${slot}-username`);
            const classInput = document.getElementById(`${slot}-class`);
            
            const infoUsername = document.getElementById(`${slot}-info-username`);
            const infoClass = document.getElementById(`${slot}-info-class`);
            const infoConverge = document.getElementById(`${slot}-info-converge`);
            const infoParity = document.getElementById(`${slot}-info-parity`);
            
            if (infoUsername) {
                const userVal = usernameInput.value.trim() || "-";
                infoUsername.innerText = isCensorActive ? `Player ${index + 1}` : userVal;
            }
            if (infoClass) {
                infoClass.innerText = classInput.value.trim() || "Standard class";
            }
            if (infoConverge) {
                infoConverge.innerText = SLOT_HARDCODED_SETTINGS[slot].converge_type.toUpperCase();
            }
            if (infoParity) {
                infoParity.innerText = SLOT_HARDCODED_SETTINGS[slot].taunt_parity.toUpperCase();
            }
            
            runningDisplay.classList.remove("hidden");
        } else {
            // Show editable inputs container
            inputsContainer.classList.remove("hidden");
            // Hide running display
            runningDisplay.classList.add("hidden");
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

    // Check if we are still within the grace period (45 seconds) to allow login
    if (lastStartTimestamp && (Date.now() - lastStartTimestamp < 45000)) {
        updateRestartStatusText("");
        return;
    }
    
    const maxAttempts = parseInt(config.auto_restart_max_attempts) || 3;

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
            addSlaveLog("System", `<span class="log-yellow log-bold">[System] Restarting party bots (Attempt ${restartAttempts}/${maxAttempts})...</span>`);
            
            setTimeout(() => {
                updateRestartStatusText("");
                startParty(true);
            }, 1000);
        }
        return;
    }

    if (isStoppingForRestart) return;
    
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

// Theme selection event listener
document.addEventListener("DOMContentLoaded", () => {
    if (!isEmbedded) {
        document.querySelectorAll(".theme-dot").forEach(dot => {
            dot.addEventListener("click", () => {
                const selectedTheme = dot.getAttribute("data-theme");
                applyTheme(selectedTheme);
                config.theme = selectedTheme;
                updateActiveThemeDot(selectedTheme);
                window.pywebview.api.save_config(config);
            });
        });
    }
});

// Password Validation Handler
document.addEventListener("DOMContentLoaded", () => {
    const passwordForm = document.getElementById("password-form");
    const passwordInput = document.getElementById("app-access-password");
    const passwordScreen = document.getElementById("password-screen");
    const passwordError = document.getElementById("password-error");
    const passwordLockIcon = document.getElementById("password-lock-icon");

    const normalFlow = document.getElementById("password-normal-flow");
    const captchaFlow = document.getElementById("password-captcha-flow");
    const gameArea = document.getElementById("captcha-game-area");
    const statusText = document.getElementById("captcha-status");

    const defaultIconHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`;
    const errorIconHTML = `<img src="error_astolfo.jpg" alt="Wrong Password" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;

    let failedAttempts = 0;
    let poppedHearts = 0;

    if (passwordForm && passwordInput && passwordScreen && passwordError) {
        // Focus the input initially
        setTimeout(() => passwordInput.focus(), 100);

        // Revert icon and hide error when typing starts
        passwordInput.addEventListener("input", () => {
            passwordError.classList.add("hidden");
            if (passwordLockIcon) {
                passwordLockIcon.innerHTML = defaultIconHTML;
                passwordLockIcon.style.borderColor = "rgba(147, 51, 234, 0.2)";
                passwordLockIcon.style.background = "rgba(147, 51, 234, 0.1)";
            }
        });

        // Scratch card implementation
        let scratchCanvas = document.getElementById("scratch-canvas");
        let scratchCtx = null;
        let isDrawing = false;
        let scratchFinished = false;

        const initScratchCard = () => {
            scratchCanvas = document.getElementById("scratch-canvas");
            if (!scratchCanvas) return;

            scratchCtx = scratchCanvas.getContext("2d");
            scratchFinished = false;
            scratchCanvas.classList.remove("fade-out");

            // Match canvas internal resolution with CSS display size
            scratchCanvas.width = scratchCanvas.clientWidth || 280;
            scratchCanvas.height = scratchCanvas.clientHeight || 320;

            // Draw metallic/dark covering layer
            const grad = scratchCtx.createLinearGradient(0, 0, scratchCanvas.width, scratchCanvas.height);
            grad.addColorStop(0, "#2d2845");
            grad.addColorStop(1, "#16122e");
            scratchCtx.fillStyle = grad;
            scratchCtx.fillRect(0, 0, scratchCanvas.width, scratchCanvas.height);

            // Add some noise texture for a scratch-card texture feel
            scratchCtx.fillStyle = "rgba(255, 255, 255, 0.03)";
            for (let i = 0; i < 2000; i++) {
                const rx = Math.random() * scratchCanvas.width;
                const ry = Math.random() * scratchCanvas.height;
                scratchCtx.fillRect(rx, ry, 2, 2);
            }

            // Draw instructing label text in middle
            scratchCtx.fillStyle = "#a855f7"; // primary purple
            scratchCtx.font = "bold 16px 'Inter', sans-serif";
            scratchCtx.textAlign = "center";
            scratchCtx.textBaseline = "middle";
            scratchCtx.fillText("SCRATCH TO REVEAL ASTOLFO", scratchCanvas.width / 2, scratchCanvas.height / 2 - 10);

            scratchCtx.fillStyle = "#9ca3af";
            scratchCtx.font = "11px 'Inter', sans-serif";
            scratchCtx.fillText("Hold & drag mouse/touch to usap", scratchCanvas.width / 2, scratchCanvas.height / 2 + 15);

            // Configure canvas to erase drawings
            scratchCtx.globalCompositeOperation = "destination-out";

            // Bind scratch events (mouse & touch)
            const scratch = (e) => {
                if (!isDrawing || scratchFinished) return;
                
                // Prevent scrolling on touch devices
                e.preventDefault();

                // Get coordinates relative to canvas
                const rect = scratchCanvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                const x = clientX - rect.left;
                const y = clientY - rect.top;

                // Erase circle
                scratchCtx.beginPath();
                scratchCtx.arc(x, y, 28, 0, Math.PI * 2);
                scratchCtx.fill();

                // Check scratch percentage occasionally
                checkProgress();
            };

            const startDrawing = (e) => {
                isDrawing = true;
                scratch(e);
            };

            const stopDrawing = () => {
                isDrawing = false;
            };

            scratchCanvas.addEventListener("mousedown", startDrawing);
            scratchCanvas.addEventListener("mousemove", scratch);
            window.addEventListener("mouseup", stopDrawing);

            scratchCanvas.addEventListener("touchstart", startDrawing, { passive: false });
            scratchCanvas.addEventListener("touchmove", scratch, { passive: false });
            window.addEventListener("touchend", stopDrawing);
        };

        const checkProgress = () => {
            if (scratchFinished || !scratchCtx) return;

            const imgData = scratchCtx.getImageData(0, 0, scratchCanvas.width, scratchCanvas.height);
            const data = imgData.data;
            let transparentCount = 0;
            const step = 20; // check every 20th pixel to prevent lagging
            let totalCount = 0;

            for (let i = 3; i < data.length; i += 4 * step) {
                totalCount++;
                if (data[i] === 0) {
                    transparentCount++;
                }
            }

            const percent = Math.round((transparentCount / totalCount) * 100);
            if (statusText) {
                statusText.innerText = `Scratch to reveal image: ${percent}% revealed`;
            }

            // Exceeds 65% scratched = revealed!
            if (percent >= 65) {
                scratchFinished = true;
                scratchCanvas.classList.add("fade-out");
                
                if (statusText) {
                    statusText.innerHTML = `<span style="color: var(--success-color)">Verification success! Resetting attempts...</span>`;
                }

                setTimeout(() => {
                    failedAttempts = 0;
                    if (captchaFlow) captchaFlow.classList.add("hidden");
                    if (normalFlow) normalFlow.classList.remove("hidden");
                    passwordInput.value = "";
                    passwordInput.focus();
                }, 1500);
            }
        };

        const startCaptchaGame = () => {
            const bgImg = document.getElementById("captcha-bg-img");
            if (bgImg) {
                const randomIndex = Math.floor(Math.random() * 3);
                bgImg.src = `astolfo_scratch${randomIndex}.png`;
            }
            if (statusText) {
                statusText.innerText = `Scratch to reveal image: 0% revealed`;
            }
            if (normalFlow) normalFlow.classList.add("hidden");
            if (captchaFlow) captchaFlow.classList.remove("hidden");
            
            // Wait brief moment for container to render so bounding rect works
            setTimeout(initScratchCard, 50);
        };

        const performCheck = (password) => {
            if (window.pywebview && window.pywebview.api && window.pywebview.api.validate_password) {
                window.pywebview.api.validate_password(password).then((res) => {
                    if (res && res.valid) {
                        passwordScreen.classList.add("hidden");
                    } else {
                        failedAttempts++;
                        if (failedAttempts >= 3) {
                            startCaptchaGame();
                        } else {
                            passwordError.innerHTML = `Incorrect password. Attempts left: ${3 - failedAttempts}`;
                            passwordError.classList.remove("hidden");
                            passwordInput.value = "";
                            passwordInput.focus();
                            if (passwordLockIcon) {
                                passwordLockIcon.innerHTML = errorIconHTML;
                                passwordLockIcon.style.borderColor = "var(--danger-color)";
                                passwordLockIcon.style.background = "rgba(239, 68, 68, 0.1)";
                            }
                        }
                    }
                }).catch((err) => {
                    console.error("Error validating password:", err);
                    alert("An error occurred during verification.");
                });
            } else {
                // If api not ready yet, wait for pywebviewready event and try again
                window.addEventListener("pywebviewready", () => {
                    performCheck(password);
                }, { once: true });
            }
        };

        passwordForm.addEventListener("submit", (e) => {
            e.preventDefault();
            performCheck(passwordInput.value);
        });
    }
});
