document.addEventListener('DOMContentLoaded', () => {
    let globalConfig = null;
    let statusInterval = null;
    let activeConsoleTab = 'System';
    let slaveLogs = { 'System': [] };
    let editingId = null;

    // Elements
    const btnStart = document.getElementById('btn-start-slaves');
    const btnStop = document.getElementById('btn-stop-slaves');
    
    // Config Inputs
    const followPlayerInput = document.getElementById('input-follow-player');
    const serverSelect = document.getElementById('select-server');
    const roomNumberInput = document.getElementById('input-room-number');
    const targetsInput = document.getElementById('input-targets-priority');
    
    // Tag Whitelist
    const newTagInput = document.getElementById('input-new-tag');
    const btnAddTag = document.getElementById('btn-add-tag');
    const whitelistTagsContainer = document.getElementById('whitelist-tags');
    
    // Patrol Locked Zones
    const newMapInput = document.getElementById('input-new-map');
    const btnAddMap = document.getElementById('btn-add-map');
    const lockedZonesContainer = document.getElementById('locked-zones-list');
    
    const btnSaveSettings = document.getElementById('btn-save-settings');

    // Account Registry Elements
    const btnToggleAddForm = document.getElementById('btn-toggle-add-form');
    const addSlaveForm = document.getElementById('add-slave-form');
    const slaveUsernameInput = document.getElementById('slave-username');
    const slavePasswordInput = document.getElementById('slave-password');
    const slaveClassInput = document.getElementById('slave-class');
    const btnSaveNewSlave = document.getElementById('btn-save-new-slave');
    const btnCancelAddSlave = document.getElementById('btn-cancel-add-slave');
    
    const slaveTableBody = document.getElementById('slave-table-body');
    const chkSelectAll = document.getElementById('chk-select-all');
    const btnDeleteSelected = document.getElementById('btn-delete-selected');

    // Console Elements
    const consoleViewport = document.getElementById('console-viewport');
    const btnClearLogs = document.getElementById('btn-clear-logs');
    const chkAutoScroll = document.getElementById('chk-auto-scroll');
    const tabsList = document.getElementById('console-tabs-list');

    // 1. Logs Stream Receiver
    window.addSlaveLog = function(username, htmlMsg) {
        if (!htmlMsg) return;
        if (!slaveLogs[username]) {
            slaveLogs[username] = [];
        }
        
        slaveLogs[username].push(htmlMsg);

        // Limit to 500 lines per tab to prevent memory overflow
        while (slaveLogs[username].length > 500) {
            slaveLogs[username].shift();
        }

        // Only append to active viewport if it matches active tab
        if (activeConsoleTab === username) {
            appendLineToConsole(htmlMsg);
        }
    };

    function appendLineToConsole(htmlMsg) {
        const line = document.createElement('div');
        line.className = 'log-line';
        line.innerHTML = htmlMsg;
        consoleViewport.appendChild(line);

        while (consoleViewport.childNodes.length > 500) {
            consoleViewport.removeChild(consoleViewport.firstChild);
        }

        if (chkAutoScroll.checked) {
            consoleViewport.scrollTop = consoleViewport.scrollHeight;
        }
    }

    function refreshConsoleViewport() {
        consoleViewport.innerHTML = '';
        const lines = slaveLogs[activeConsoleTab] || [];
        lines.forEach(line => {
            appendLineToConsole(line);
        });
    }

    btnClearLogs.addEventListener('click', () => {
        slaveLogs[activeConsoleTab] = [];
        consoleViewport.innerHTML = `<div class="log-line system">Logs for ${activeConsoleTab} cleared.</div>`;
    });

    // Console Tab Switch handler
    tabsList.addEventListener('click', (e) => {
        const tabBtn = e.target.closest('.console-tab');
        if (!tabBtn) return;
        
        tabsList.querySelectorAll('.console-tab').forEach(t => t.classList.remove('active'));
        tabBtn.classList.add('active');
        
        activeConsoleTab = tabBtn.getAttribute('data-source');
        refreshConsoleViewport();
    });

    function renderConsoleTabs() {
        tabsList.innerHTML = '';
        
        // System tab is always first
        const systemBtn = document.createElement('button');
        systemBtn.className = `console-tab ${activeConsoleTab === 'System' ? 'active' : ''}`;
        systemBtn.setAttribute('data-source', 'System');
        systemBtn.textContent = 'System';
        tabsList.appendChild(systemBtn);
        
        const slaves = globalConfig ? (globalConfig.slaves || []) : [];
        slaves.forEach(s => {
            const btn = document.createElement('button');
            btn.className = `console-tab ${activeConsoleTab === s.username ? 'active' : ''}`;
            btn.setAttribute('data-source', s.username);
            btn.textContent = s.username;
            tabsList.appendChild(btn);
        });
    }

    // 2. Toggle Forms
    btnToggleAddForm.addEventListener('click', () => {
        addSlaveForm.classList.toggle('hidden');
    });

    btnCancelAddSlave.addEventListener('click', () => {
        addSlaveForm.classList.add('hidden');
        clearAddFormInputs();
        
        // Reset edit states if any
        editingId = null;
        document.getElementById('add-slave-title').textContent = 'Add New Slave Account';
        btnSaveNewSlave.textContent = 'Save Account';
        slaveUsernameInput.disabled = false;
    });

    function clearAddFormInputs() {
        slaveUsernameInput.value = '';
        slavePasswordInput.value = '';
        slaveClassInput.value = '';
    }

    // 3. Checklist & Whitelist Managers
    function renderWhitelistTags() {
        whitelistTagsContainer.innerHTML = '';
        const isRunning = btnStart.classList.contains('hidden');
        const items = globalConfig.whitelist || [];
        items.forEach((item, index) => {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.innerHTML = `${item} <button class="btn-tag-remove" data-index="${index}" ${isRunning ? 'disabled' : ''}>&times;</button>`;
            whitelistTagsContainer.appendChild(tag);
        });
    }

    whitelistTagsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-tag-remove')) {
            const index = parseInt(e.target.getAttribute('data-index'));
            globalConfig.whitelist.splice(index, 1);
            renderWhitelistTags();
        }
    });

    btnAddTag.addEventListener('click', () => {
        const val = newTagInput.value.trim();
        if (val && !globalConfig.whitelist.includes(val)) {
            globalConfig.whitelist.push(val);
            renderWhitelistTags();
            newTagInput.value = '';
        }
    });

    function renderPatrolPatches() {
        lockedZonesContainer.innerHTML = '';
        const maps = globalConfig.locked_zones || [];
        maps.forEach(map => {
            const label = document.createElement('label');
            label.className = 'checklist-item';
            label.innerHTML = `<input type="checkbox" class="chk-map" value="${map}" checked> ${map}`;
            lockedZonesContainer.appendChild(label);
        });
    }

    btnAddMap.addEventListener('click', () => {
        const mapName = newMapInput.value.trim().toLowerCase();
        if (mapName && !globalConfig.locked_zones.includes(mapName)) {
            globalConfig.locked_zones.push(mapName);
            renderPatrolPatches();
            newMapInput.value = '';
        }
    });

    // 4. Accounts Table Highlight Toggles
    chkSelectAll.addEventListener('change', () => {
        const chks = slaveTableBody.querySelectorAll('.chk-slave');
        chks.forEach(c => {
            c.checked = chkSelectAll.checked;
            const tr = c.closest('tr');
            if (tr) {
                if (chkSelectAll.checked) {
                    tr.classList.add('row-checked');
                } else {
                    tr.classList.remove('row-checked');
                }
            }
        });
    });

    slaveTableBody.addEventListener('change', (e) => {
        if (e.target.classList.contains('chk-slave')) {
            const tr = e.target.closest('tr');
            if (tr) {
                if (e.target.checked) {
                    tr.classList.add('row-checked');
                } else {
                    tr.classList.remove('row-checked');
                }
            }
        }
    });

    btnDeleteSelected.addEventListener('click', () => {
        const chks = slaveTableBody.querySelectorAll('.chk-slave:checked');
        if (chks.length === 0) {
            alert('Please select slave accounts to delete.');
            return;
        }
        
        if (confirm(`Are you sure you want to delete these ${chks.length} accounts?`)) {
            const deleteIds = Array.from(chks).map(c => c.value);
            globalConfig.slaves = globalConfig.slaves.filter(s => !deleteIds.includes(s.id));
            saveConfigurationLocal(true);
        }
    });

    function generateUniqueId() {
        return 'id_' + Math.random().toString(36).substring(2, 9) + Date.now().toString(36).substring(4);
    }

    btnSaveNewSlave.addEventListener('click', () => {
        const user = slaveUsernameInput.value.trim();
        const pass = slavePasswordInput.value;
        const cls = slaveClassInput.value.trim();

        if (!user || !pass || !cls) {
            alert('Please fill all slave account credentials.');
            return;
        }

        if (editingId) {
            // Edit Mode: check if username already exists in *other* accounts
            if (globalConfig.slaves.some(s => s.id !== editingId && s.username.toLowerCase() === user.toLowerCase())) {
                alert('This slave account username already exists in registry.');
                return;
            }

            const slaveIdx = globalConfig.slaves.findIndex(s => s.id === editingId);
            if (slaveIdx !== -1) {
                const oldUsername = globalConfig.slaves[slaveIdx].username;
                
                globalConfig.slaves[slaveIdx] = {
                    id: editingId,
                    username: user,
                    password: pass,
                    char_class: cls
                };
                
                // If username changed, update keys in logs map
                if (user !== oldUsername) {
                    if (slaveLogs[oldUsername]) {
                        slaveLogs[user] = slaveLogs[oldUsername];
                        delete slaveLogs[oldUsername];
                    }
                    if (activeConsoleTab === oldUsername) {
                        activeConsoleTab = user;
                    }
                }
            }
            
            // Reset edit states
            editingId = null;
            document.getElementById('add-slave-title').textContent = 'Add New Slave Account';
            btnSaveNewSlave.textContent = 'Save Account';
        } else {
            // Add Mode
            if (globalConfig.slaves.some(s => s.username.toLowerCase() === user.toLowerCase())) {
                alert('This slave account username already exists in registry.');
                return;
            }

            const newId = generateUniqueId();
            globalConfig.slaves.push({
                id: newId,
                username: user,
                password: pass,
                char_class: cls
            });

            if (!slaveLogs[user]) {
                slaveLogs[user] = [];
            }
        }

        saveConfigurationLocal(true);
        addSlaveForm.classList.add('hidden');
        clearAddFormInputs();
    });

    // 5. Integration Hooks
    if (window.pywebview && window.pywebview.api) {
        initApp();
    } else {
        window.addEventListener('pywebviewready', () => {
            initApp();
        });
    }

    function initApp() {
        loadUserConfig();
        startStatusPolling();
    }

    function loadUserConfig() {
        window.pywebview.api.load_config().then(config => {
            globalConfig = config;
            
            followPlayerInput.value = config.follow_player || '';
            serverSelect.value = config.server || 'Artix';
            roomNumberInput.value = config.room_number || 9099;
            targetsInput.value = config.targets_priority || '';
            
            // Backport unique IDs to existing accounts
            const slaves = globalConfig.slaves || [];
            slaves.forEach(s => {
                if (!s.id) {
                    s.id = generateUniqueId();
                }
            });

            // Pre-initialize logs objects
            if (!slaveLogs['System']) slaveLogs['System'] = [];
            slaves.forEach(s => {
                if (!slaveLogs[s.username]) {
                    slaveLogs[s.username] = [];
                }
            });

            renderWhitelistTags();
            renderPatrolPatches();
            renderSlavesTable();
            renderConsoleTabs();
        });
    }

    function renderSlavesTable() {
        slaveTableBody.innerHTML = '';
        const slaves = globalConfig.slaves || [];
        
        if (slaves.length === 0) {
            slaveTableBody.innerHTML = `<tr><td colspan="7" class="text-muted" style="text-align: center; padding: 20px;">No registered slave accounts. Click "+ Add Account" to start.</td></tr>`;
            return;
        }

        slaves.forEach(s => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-username', s.username);
            tr.id = `slave-row-${s.id}`;
            tr.innerHTML = `
                <td><input type="checkbox" class="chk-slave" value="${s.id}"></td>
                <td><strong>${s.username}</strong></td>
                <td><span class="text-muted">${s.char_class}</span></td>
                <td class="col-map">-</td>
                <td class="col-vitals">
                    <div class="vitals-progress-wrapper">
                        <div class="mini-vital-bar">
                            <div class="mini-hp-fill" id="hp-bar-${s.id}"></div>
                        </div>
                        <div class="mini-vital-bar">
                            <div class="mini-mp-fill" id="mp-bar-${s.id}"></div>
                        </div>
                        <div class="vital-labels-sm">
                            <span id="hp-txt-${s.id}">0/0</span>
                            <span id="mp-txt-${s.id}">0/0</span>
                        </div>
                    </div>
                </td>
                <td class="col-status"><span class="status-pill offline">Offline</span></td>
                <td>
                    <select class="select-action" data-id="${s.id}">
                        <option value="" disabled selected>Actions</option>
                        <option value="edit">Edit</option>
                        <option value="delete">Delete</option>
                    </select>
                </td>
            `;
            slaveTableBody.appendChild(tr);
        });
    }

    slaveTableBody.addEventListener('change', (e) => {
        if (e.target.classList.contains('select-action')) {
            const action = e.target.value;
            const id = e.target.getAttribute('data-id');
            const slave = globalConfig.slaves.find(s => s.id === id);
            
            if (!slave) return;
            
            if (action === 'delete') {
                if (confirm(`Delete account ${slave.username}?`)) {
                    globalConfig.slaves = globalConfig.slaves.filter(s => s.id !== id);
                    saveConfigurationLocal(true);
                } else {
                    e.target.value = "";
                }
            } else if (action === 'edit') {
                // Open and set form in edit mode
                editingId = id;
                
                slaveUsernameInput.value = slave.username;
                slavePasswordInput.value = slave.password;
                slaveClassInput.value = slave.char_class;
                
                document.getElementById('add-slave-title').textContent = 'Edit Slave Account';
                btnSaveNewSlave.textContent = 'Update Account';
                
                slaveUsernameInput.disabled = false;
                
                addSlaveForm.classList.remove('hidden');
                addSlaveForm.scrollIntoView({ behavior: 'smooth' });
                
                e.target.value = "";
            }
        }
    });

    function compileFormConfig() {
        const checkedMaps = Array.from(lockedZonesContainer.querySelectorAll('.chk-map:checked')).map(c => c.value);
        
        globalConfig.follow_player = followPlayerInput.value.trim();
        globalConfig.server = serverSelect.value;
        globalConfig.room_number = parseInt(roomNumberInput.value) || 9099;
        globalConfig.targets_priority = targetsInput.value.trim();
        globalConfig.locked_zones = checkedMaps;
    }

    function saveConfigurationLocal(reRender = false) {
        compileFormConfig();
        window.pywebview.api.save_config(globalConfig).then(res => {
            if (res.success) {
                if (reRender) {
                    renderSlavesTable();
                    renderConsoleTabs();
                }
            } else {
                alert(`Error saving configurations: ${res.error}`);
            }
        });
    }

    btnSaveSettings.addEventListener('click', () => {
        saveConfigurationLocal();
        alert('Configuration settings saved successfully.');
    });

    // 6. Form Locking when active
    function setUIStateRunning(isRunning) {
        btnToggleAddForm.disabled = isRunning;
        btnDeleteSelected.disabled = isRunning;
        btnSaveSettings.disabled = isRunning;
        chkSelectAll.disabled = isRunning;

        followPlayerInput.disabled = isRunning;
        serverSelect.disabled = isRunning;
        roomNumberInput.disabled = isRunning;
        targetsInput.disabled = isRunning;
        newTagInput.disabled = isRunning;
        btnAddTag.disabled = isRunning;
        newMapInput.disabled = isRunning;
        btnAddMap.disabled = isRunning;

        const mapChks = lockedZonesContainer.querySelectorAll('.chk-map');
        mapChks.forEach(c => c.disabled = isRunning);

        const tagRemoves = whitelistTagsContainer.querySelectorAll('.btn-tag-remove');
        tagRemoves.forEach(btn => btn.disabled = isRunning);

        const slaveChks = slaveTableBody.querySelectorAll('.chk-slave');
        slaveChks.forEach(c => c.disabled = isRunning);

        const actionSelects = slaveTableBody.querySelectorAll('.select-action');
        actionSelects.forEach(sel => sel.disabled = isRunning);
        
        if (isRunning) {
            addSlaveForm.classList.add('hidden');
        }
    }

    // 7. Bot Launchers Control
    btnStart.addEventListener('click', () => {
        compileFormConfig();
        
        const checkedChks = slaveTableBody.querySelectorAll('.chk-slave:checked');
        if (checkedChks.length === 0) {
            alert('Please select at least one slave account to start!');
            return;
        }

        if (!globalConfig.follow_player) {
            alert('Master Player Name is required to start the follow bots!');
            followPlayerInput.focus();
            return;
        }

        const selectedIds = Array.from(checkedChks).map(c => c.value);
        const selectedUsernames = selectedIds.map(id => {
            const s = globalConfig.slaves.find(s => s.id === id);
            return s ? s.username : null;
        }).filter(u => u !== null);
        
        btnStart.disabled = true;
        btnStart.textContent = 'Launching...';

        window.pywebview.api.start_slaves(globalConfig, selectedUsernames).then(res => {
            btnStart.disabled = false;
            btnStart.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg> Start Selected Slaves
            `;
            if (res.success) {
                btnStart.classList.add('hidden');
                btnStop.classList.remove('hidden');
                setUIStateRunning(true);
                
                // Jump to the first selected slave tab automatically to show output
                activeConsoleTab = selectedUsernames[0];
                renderConsoleTabs();
                refreshConsoleViewport();
            } else {
                alert(`Failed to start slaves: ${res.error}`);
            }
        });
    });

    btnStop.addEventListener('click', () => {
        btnStop.disabled = true;
        btnStop.textContent = 'Stopping...';
        
        window.pywebview.api.stop_slaves().then(res => {
            btnStop.disabled = false;
            btnStop.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                    <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
                </svg> Stop All Slaves
            `;
            if (res.success) {
                btnStop.classList.add('hidden');
                btnStart.classList.remove('hidden');
                setUIStateRunning(false);
                
                globalConfig.slaves.forEach(s => {
                    updateRowStatus(s.username, { running: false, is_connected: false });
                });
            } else {
                alert(`Error stopping bots: ${res.error}`);
            }
        });
    });

    // 8. Polling Telemetry status
    function startStatusPolling() {
        if (statusInterval) clearInterval(statusInterval);
        
        statusInterval = setInterval(() => {
            if (!window.pywebview || !window.pywebview.api) return;

            window.pywebview.api.get_status().then(statuses => {
                let anyRunning = false;
                
                globalConfig.slaves.forEach(s => {
                    const status = statuses[s.username];
                    if (status) {
                        updateRowStatus(s.username, status);
                        if (status.running) anyRunning = true;
                    } else {
                        updateRowStatus(s.username, { running: false, is_connected: false });
                    }
                });

                if (anyRunning) {
                    btnStart.classList.add('hidden');
                    btnStop.classList.remove('hidden');
                    setUIStateRunning(true);
                } else {
                    btnStop.classList.add('hidden');
                    btnStart.classList.remove('hidden');
                    setUIStateRunning(false);
                }
            }).catch(err => {
                console.error("Status telemetry update failed", err);
            });
        }, 1000);
    }

    function updateRowStatus(username, status) {
        const row = document.querySelector(`.slave-table tbody tr[data-username="${username}"]`);
        if (!row) return;

        const colMap = row.querySelector('.col-map');
        const colStatus = row.querySelector('.col-status');
        
        const slave = globalConfig.slaves.find(s => s.username === username);
        if (!slave) return;
        const id = slave.id;

        const hpBar = document.getElementById(`hp-bar-${id}`);
        const mpBar = document.getElementById(`mp-bar-${id}`);
        const hpTxt = document.getElementById(`hp-txt-${id}`);
        const mpTxt = document.getElementById(`mp-txt-${id}`);

        if (!status || !status.running) {
            colMap.textContent = '-';
            colStatus.innerHTML = `<span class="status-pill offline">Offline</span>`;
            if (hpBar) hpBar.style.width = '0%';
            if (mpBar) mpBar.style.width = '0%';
            if (hpTxt) hpTxt.textContent = '0/0';
            if (mpTxt) mpTxt.textContent = '0/0';
            return;
        }

        colMap.textContent = `${status.map} (${status.cell})`;

        if (status.is_dead) {
            colStatus.innerHTML = `<span class="status-pill dead">Dead</span>`;
        } else if (status.is_connected) {
            colStatus.innerHTML = `<span class="status-pill online">Farming</span>`;
        } else {
            colStatus.innerHTML = `<span class="status-pill connecting">Connecting</span>`;
        }

        if (hpBar && status.max_hp > 0) {
            const hpPercent = (status.hp / status.max_hp) * 100;
            hpBar.style.width = `${Math.min(100, Math.max(0, hpPercent))}%`;
            hpTxt.textContent = `${status.hp}/${status.max_hp}`;
        }
        if (mpBar && status.max_mp > 0) {
            const mpPercent = (status.mp / status.max_mp) * 100;
            mpBar.style.width = `${Math.min(100, Math.max(0, mpPercent))}%`;
            mpTxt.textContent = `${status.mp}/${status.max_mp}`;
        }
    }
});
