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
    const copyWalkInput = document.getElementById('input-copy-walk');
    const serverSelect = document.getElementById('select-server');
    const roomNumberInput = document.getElementById('input-room-number');
    const targetsInput = document.getElementById('input-targets-priority');
    const autoZoneSelect = document.getElementById('select-auto-zone');
    
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
    const slaveSkillsInput = document.getElementById('slave-skills');
    const slaveHpOperatorSelect = document.getElementById('slave-hp-operator');
    const slaveHpThresholdInput = document.getElementById('slave-hp-threshold');
    const slaveHpSkillsInput = document.getElementById('slave-hp-skills');
    const slaveMpOperatorSelect = document.getElementById('slave-mp-operator');
    const slaveMpThresholdInput = document.getElementById('slave-mp-threshold');
    const slaveMpSkillsInput = document.getElementById('slave-mp-skills');
    const btnSaveNewSlave = document.getElementById('btn-save-new-slave');
    const btnCancelAddSlave = document.getElementById('btn-cancel-add-slave');
    
    const slaveTableBody = document.getElementById('slave-table-body');
    const chkSelectAll = document.getElementById('chk-select-all');

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

    const btnToggleTheme = document.getElementById('btn-toggle-theme');
    if (btnToggleTheme) {
        btnToggleTheme.addEventListener('click', () => {
            const active = document.body.classList.toggle('theme-maid');
            if (globalConfig) {
                globalConfig.theme_maid = active;
                window.pywebview.api.save_config(globalConfig);
            }
        });
    }

    const btnToggleSettings = document.getElementById('btn-toggle-settings');
    const appBody = document.getElementById('app-body');
    if (btnToggleSettings && appBody) {
        btnToggleSettings.addEventListener('click', () => {
            const active = appBody.classList.toggle('settings-hidden');
            btnToggleSettings.classList.toggle('active', active);
            if (globalConfig) {
                globalConfig.settings_hidden = active;
                window.pywebview.api.save_config(globalConfig);
            }
        });
    }

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
        addSlaveForm.classList.remove('hidden');
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

    const btnCloseSlaveModal = document.getElementById('btn-close-slave-modal');
    if (btnCloseSlaveModal) {
        btnCloseSlaveModal.addEventListener('click', () => {
            btnCancelAddSlave.click();
        });
    }

    addSlaveForm.addEventListener('click', (e) => {
        if (e.target === addSlaveForm) {
            btnCancelAddSlave.click();
        }
    });

    function clearAddFormInputs() {
        slaveUsernameInput.value = '';
        slavePasswordInput.value = '';
        slaveClassInput.value = '';
        slaveSkillsInput.value = '1,2,3,4';
        slaveHpThresholdInput.value = '';
        slaveHpSkillsInput.value = '';
        slaveMpThresholdInput.value = '';
        slaveMpSkillsInput.value = '';
        slaveHpOperatorSelect.value = '<';
        slaveMpOperatorSelect.value = '<';
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

    // Deleted btnDeleteSelected handler

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
                    char_class: cls,
                    skills: slaveSkillsInput.value.trim() || '1,2,3,4',
                    hp_operator: slaveHpOperatorSelect.value,
                    hp_threshold: parseInt(slaveHpThresholdInput.value) || 0,
                    hp_skills: slaveHpSkillsInput.value.trim() || '',
                    mp_operator: slaveMpOperatorSelect.value,
                    mp_threshold: parseInt(slaveMpThresholdInput.value) || 0,
                    mp_skills: slaveMpSkillsInput.value.trim() || ''
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
                char_class: cls,
                skills: slaveSkillsInput.value.trim() || '1,2,3,4',
                hp_operator: slaveHpOperatorSelect.value,
                hp_threshold: parseInt(slaveHpThresholdInput.value) || 0,
                hp_skills: slaveHpSkillsInput.value.trim() || '',
                mp_operator: slaveMpOperatorSelect.value,
                mp_threshold: parseInt(slaveMpThresholdInput.value) || 0,
                mp_skills: slaveMpSkillsInput.value.trim() || ''
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
            
            // Apply saved settings panel state
            const isSettingsHidden = config.settings_hidden || false;
            if (isSettingsHidden) {
                appBody.classList.add('settings-hidden');
                btnToggleSettings.classList.add('active');
            } else {
                appBody.classList.remove('settings-hidden');
                btnToggleSettings.classList.remove('active');
            }

            // Apply saved theme state
            const isMaidTheme = config.theme_maid || false;
            if (isMaidTheme) {
                document.body.classList.add('theme-maid');
            } else {
                document.body.classList.remove('theme-maid');
            }

            followPlayerInput.value = config.follow_player || '';
            copyWalkInput.checked = config.copy_walk !== undefined ? config.copy_walk : true;
            serverSelect.value = config.server || 'Artix';
            roomNumberInput.value = config.room_number || 9099;
            targetsInput.value = config.targets_priority || '';
            autoZoneSelect.value = config.auto_zone || 'none';
            
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
            slaveTableBody.innerHTML = `<tr><td colspan="8" class="text-muted" style="text-align: center; padding: 20px;">No registered slave accounts. Click "+ Add Account" to start.</td></tr>`;
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
                <td class="col-recent-skills">
                    <div class="recent-skills-container" id="recent-skills-${s.id}">
                        <span class="text-muted">-</span>
                    </div>
                </td>
                <td class="col-status"><span class="status-pill offline">Offline</span></td>
                <td style="position: relative; text-align: center;">
                    <button class="btn-action-trigger" data-id="${s.id}" title="Actions">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" style="pointer-events: none; display: block; margin: 0 auto;">
                            <circle cx="12" cy="5" r="2.2"></circle>
                            <circle cx="12" cy="12" r="2.2"></circle>
                            <circle cx="12" cy="19" r="2.2"></circle>
                        </svg>
                    </button>
                    <div class="action-dropdown hidden" id="action-dropdown-${s.id}">
                        <button class="action-item edit" data-action="edit" data-id="${s.id}">Edit</button>
                        <button class="action-item delete" data-action="delete" data-id="${s.id}">Delete</button>
                    </div>
                </td>
            `;
            slaveTableBody.appendChild(tr);
        });
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.btn-action-trigger')) {
            document.querySelectorAll('.action-dropdown').forEach(d => d.classList.add('hidden'));
        }
    });

    slaveTableBody.addEventListener('click', (e) => {
        // Toggle dropdown visibility
        if (e.target.closest('.btn-action-trigger')) {
            const btn = e.target.closest('.btn-action-trigger');
            const id = btn.getAttribute('data-id');
            const dropdown = document.getElementById(`action-dropdown-${id}`);
            
            // Close other dropdowns
            document.querySelectorAll('.action-dropdown').forEach(d => {
                if (d !== dropdown) d.classList.add('hidden');
            });
            
            if (dropdown) {
                dropdown.classList.toggle('hidden');
            }
            return;
        }

        // Handle action item click
        if (e.target.classList.contains('action-item')) {
            const action = e.target.getAttribute('data-action');
            const id = e.target.getAttribute('data-id');
            const slave = globalConfig.slaves.find(s => s.id === id);
            
            // Close dropdown
            const dropdown = document.getElementById(`action-dropdown-${id}`);
            if (dropdown) dropdown.classList.add('hidden');

            if (!slave) return;

            if (action === 'delete') {
                if (confirm(`Delete account ${slave.username}?`)) {
                    globalConfig.slaves = globalConfig.slaves.filter(s => s.id !== id);
                    saveConfigurationLocal(true);
                }
            } else if (action === 'edit') {
                // Open and set form in edit mode
                editingId = id;
                
                slaveUsernameInput.value = slave.username;
                slavePasswordInput.value = slave.password;
                slaveClassInput.value = slave.char_class;
                slaveSkillsInput.value = slave.skills || '1,2,3,4';
                slaveHpOperatorSelect.value = slave.hp_operator || '<';
                slaveHpThresholdInput.value = slave.hp_threshold !== undefined ? slave.hp_threshold : '';
                slaveHpSkillsInput.value = slave.hp_skills || '';
                slaveMpOperatorSelect.value = slave.mp_operator || '<';
                slaveMpThresholdInput.value = slave.mp_threshold !== undefined ? slave.mp_threshold : '';
                slaveMpSkillsInput.value = slave.mp_skills || '';
                
                document.getElementById('add-slave-title').textContent = 'Edit Slave Account';
                btnSaveNewSlave.textContent = 'Update Account';
                
                slaveUsernameInput.disabled = false;
                
                addSlaveForm.classList.remove('hidden');
            }
        }
    });

    function compileFormConfig() {
        const checkedMaps = Array.from(lockedZonesContainer.querySelectorAll('.chk-map:checked')).map(c => c.value);
        
        globalConfig.follow_player = followPlayerInput.value.trim();
        globalConfig.copy_walk = copyWalkInput.checked;
        globalConfig.server = serverSelect.value;
        globalConfig.room_number = parseInt(roomNumberInput.value) || 9099;
        globalConfig.targets_priority = targetsInput.value.trim();
        globalConfig.auto_zone = autoZoneSelect.value;
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
        btnSaveSettings.disabled = isRunning;
        chkSelectAll.disabled = isRunning;

        followPlayerInput.disabled = isRunning;
        copyWalkInput.disabled = isRunning;
        serverSelect.disabled = isRunning;
        roomNumberInput.disabled = isRunning;
        targetsInput.disabled = isRunning;
        autoZoneSelect.disabled = isRunning;
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
        const recentSkillsEl = document.getElementById(`recent-skills-${id}`);

        if (!status || !status.running) {
            colMap.textContent = '-';
            colStatus.innerHTML = `<span class="status-pill offline">Offline</span>`;
            if (hpBar) hpBar.style.width = '0%';
            if (mpBar) mpBar.style.width = '0%';
            if (hpTxt) hpTxt.textContent = '0/0';
            if (mpTxt) mpTxt.textContent = '0/0';
            if (recentSkillsEl) {
                recentSkillsEl.innerHTML = '<span class="text-muted">-</span>';
            }
            return;
        }

        colMap.textContent = `${status.map} (${status.cell})`;

        if (status.is_dead) {
            colStatus.innerHTML = `<span class="status-pill dead">Dead</span>`;
        } else if (status.is_connected) {
            colStatus.innerHTML = `<span class="status-pill online">Serving</span>`;
        } else {
            colStatus.innerHTML = `<span class="status-pill connecting">Connecting</span>`;
        }

        if (recentSkillsEl) {
            const skills = status.last_skills || [];
            if (skills.length === 0) {
                recentSkillsEl.innerHTML = '<span class="text-muted">-</span>';
            } else {
                recentSkillsEl.innerHTML = skills.map(sk => `<span class="recent-skill-pill">${sk}</span>`).join('');
            }
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

    // Dynamic Versioning check
    window.addEventListener('pywebviewready', async () => {
        try {
            if (window.pywebview && window.pywebview.api && window.pywebview.api.get_version) {
                const version = await window.pywebview.api.get_version();
                const verEl = document.getElementById('app-version');
                if (verEl && version) {
                    verEl.textContent = version;
                }
            }
        } catch (err) {
            console.log("Could not fetch version:", err);
        }
    });
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
});

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
