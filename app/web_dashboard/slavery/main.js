document.addEventListener('DOMContentLoaded', () => {


    let globalConfig = null;
    let statusInterval = null;
    let activeConsoleTab = 'System';
    let slaveLogs = { 'System': [] };
    let editingId = null;

    const isEmbedded = window.parent && window.parent !== window;

    function applyTheme(themeName) {
        if (isEmbedded) return;
        document.body.classList.remove("theme-red", "theme-pink", "theme-blue", "theme-green");
        if (themeName !== "default") {
            document.body.classList.add(`theme-${themeName}`);
        }
        if (globalConfig) {
            globalConfig.theme = themeName;
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

    // Elements
    const btnStart = document.getElementById('btn-start-slaves');
    const btnStop = document.getElementById('btn-stop-slaves');
    const btnPause = document.getElementById('btn-pause-slaves');
    let isPausedState = false;

    // Config Inputs
    const followPlayerInput = document.getElementById('input-follow-player');
    const copyWalkInput = document.getElementById('input-copy-walk');
    const serverSelectEl = document.getElementById('select-server');
    const serverSelect = serverSelectEl ? (serverSelectEl.querySelector('select') || serverSelectEl) : null;
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
    const slaveTaunterInput = document.getElementById('slave-taunter');
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
    window.addSlaveLog = function (username, htmlMsg) {
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



    // Toast notification helper
    function showToast(message) {
        const toast = document.getElementById('toast-notification');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 2500);
    }

    // Global Settings Modal Dialog
    const modalGlobalSettings = document.getElementById('modal-global-settings');
    const btnToggleSettings = document.getElementById('btn-toggle-settings');
    const btnCloseSettingsModal = document.getElementById('btn-close-settings-modal');
    const btnCancelSettings = document.getElementById('btn-cancel-settings');

    function openGlobalSettingsModal() {
        if (modalGlobalSettings) {
            modalGlobalSettings.classList.remove('hidden');
        }
    }

    function closeGlobalSettingsModal() {
        if (modalGlobalSettings) {
            modalGlobalSettings.classList.add('hidden');
        }
    }

    if (btnToggleSettings) {
        btnToggleSettings.addEventListener('click', openGlobalSettingsModal);
    }
    if (btnCloseSettingsModal) {
        btnCloseSettingsModal.addEventListener('click', closeGlobalSettingsModal);
    }
    if (btnCancelSettings) {
        btnCancelSettings.addEventListener('click', closeGlobalSettingsModal);
    }
    if (modalGlobalSettings) {
        modalGlobalSettings.addEventListener('click', (e) => {
            if (e.target === modalGlobalSettings) {
                closeGlobalSettingsModal();
            }
        });
    }

    // Modal Tabs Navigation
    const modalSettingsTabs = document.querySelectorAll('#modal-global-settings .modal-tab');
    const modalSettingsContents = document.querySelectorAll('#modal-global-settings .modal-tab-content');
    modalSettingsTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            modalSettingsTabs.forEach(t => t.classList.remove('active'));
            modalSettingsContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const targetContent = document.getElementById(targetTab);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
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
        slaveTaunterInput.checked = false;
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
        if (e.target.classList.contains('chk-taunt-toggle')) {
            const id = e.target.getAttribute('data-id');
            const checked = e.target.checked;
            const slave = globalConfig.slaves.find(s => s.id === id);
            if (slave) {
                slave.taunter = checked;
                saveConfigurationLocal(false);
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
                    taunter: slaveTaunterInput.checked,
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
                taunter: slaveTaunterInput.checked,
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



            if (!isEmbedded) {
                const savedTheme = config.theme || "default";
                updateActiveThemeDot(savedTheme);
                applyTheme(savedTheme);
            } else {
                const selectorGroup = document.getElementById("theme-selector-group");
                if (selectorGroup) selectorGroup.style.display = "none";
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
        const badgeCount = document.getElementById('badge-slave-count');
        if (badgeCount) {
            badgeCount.textContent = `${slaves.length} Accounts`;
        }

        if (slaves.length === 0) {
            slaveTableBody.innerHTML = `<tr><td colspan="9" class="text-muted" style="text-align: center; padding: 20px;">No registered slave accounts. Click "+ Add Account" to start.</td></tr>`;
            return;
        }

        slaves.forEach(s => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-username', s.username);
            tr.innerHTML = `
                <td class="col-chk" style="text-align: center;">
                    <input type="checkbox" class="chk-slave" value="${s.id}">
                </td>
                <td class="col-account">
                    <div class="account-cell">
                        <div class="account-meta">
                            <span class="account-name">${s.username}</span>
                            <span class="account-sub">Skills: ${s.skills || '1,2,3,4'}</span>
                        </div>
                    </div>
                </td>
                <td class="col-class">
                    <div class="class-badge" title="${s.char_class || 'Default'}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="class-badge-icon">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        </svg>
                        <span class="class-badge-text">${s.char_class || 'Default'}</span>
                    </div>
                </td>
                <td class="col-taunt" style="text-align: center;">
                    <div class="taunt-cell-wrapper">
                        <label class="mini-switch" title="Auto Loop Taunt (Scroll of Enrage)">
                            <input type="checkbox" class="chk-taunt-toggle" data-id="${s.id}" ${s.taunter ? 'checked' : ''}>
                            <span class="mini-switch-slider"></span>
                        </label>
                        <span id="scroll-qty-${s.id}" class="scroll-qty-badge" style="display: none;">0 SoE</span>
                    </div>
                </td>
                <td class="col-map">
                    <div class="location-chip" id="location-chip-${s.id}">
                        <span class="text-muted">-</span>
                    </div>
                </td>
                <td class="col-vitals">
                    <div class="vitals-progress-wrapper">
                        <div class="vital-row">
                            <span class="vital-tag tag-hp">HP</span>
                            <div class="mini-vital-bar">
                                <div class="mini-hp-fill" id="hp-bar-${s.id}"></div>
                            </div>
                            <span class="vital-val" id="hp-txt-${s.id}">0/0</span>
                        </div>
                        <div class="vital-row">
                            <span class="vital-tag tag-mp">MP</span>
                            <div class="mini-vital-bar">
                                <div class="mini-mp-fill" id="mp-bar-${s.id}"></div>
                            </div>
                            <span class="vital-val" id="mp-txt-${s.id}">0/0</span>
                        </div>
                    </div>
                </td>
                <td class="col-recent-skills">
                    <div class="recent-skills-container" id="recent-skills-${s.id}">
                        <span class="text-muted cd-placeholder">-</span>
                    </div>
                </td>
                <td class="col-status">
                    <span class="status-pill offline">
                        <span class="status-pill-dot"></span>
                        <span class="status-pill-text">Offline</span>
                    </span>
                </td>
                <td class="col-action" style="position: relative; text-align: center;">
                    <div class="col-action-wrapper">
                        <button class="btn-action-telemetry" type="button" data-id="${s.id}" data-username="${s.username}" title="Player Telemetry">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                            </svg>
                        </button>
                        <button class="btn-action-trigger" type="button" data-id="${s.id}" title="Actions">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                                <circle cx="12" cy="5" r="2.2"></circle>
                                <circle cx="12" cy="12" r="2.2"></circle>
                                <circle cx="12" cy="19" r="2.2"></circle>
                            </svg>
                        </button>
                        <div class="action-dropdown hidden" id="action-dropdown-${s.id}">
                            <button class="action-item edit" data-action="edit" data-id="${s.id}">
                                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                </svg>
                                <span>Edit</span>
                            </button>
                            <button class="action-item delete" data-action="delete" data-id="${s.id}">
                                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                                <span>Delete</span>
                            </button>
                        </div>
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
        // Direct telemetry icon click
        const telBtn = e.target.closest('.btn-action-telemetry');
        if (telBtn) {
            e.stopPropagation();
            let username = telBtn.getAttribute('data-username');
            if (!username) {
                const id = telBtn.getAttribute('data-id');
                const slave = (globalConfig && Array.isArray(globalConfig.slaves)) ? globalConfig.slaves.find(s => String(s.id) === String(id)) : null;
                if (slave) username = slave.username;
            }
            openTelemetryModal(username);
            return;
        }

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

        // Handle action item click (Edit, Delete)
        const actionItem = e.target.closest('.action-item');
        if (actionItem) {
            const action = actionItem.getAttribute('data-action');
            const id = actionItem.getAttribute('data-id');
            const slave = (globalConfig && Array.isArray(globalConfig.slaves)) ? globalConfig.slaves.find(s => String(s.id) === String(id)) : null;

            // Close dropdown
            const dropdown = document.getElementById(`action-dropdown-${id}`);
            if (dropdown) dropdown.classList.add('hidden');

            if (!slave) return;

            if (action === 'delete') {
                if (confirm(`Delete account ${slave.username}?`)) {
                    globalConfig.slaves = globalConfig.slaves.filter(s => String(s.id) !== String(id));
                    saveConfigurationLocal(true);
                }
            } else if (action === 'edit') {
                // Open and set form in edit mode
                editingId = id;

                slaveUsernameInput.value = slave.username;
                slavePasswordInput.value = slave.password;
                slaveClassInput.value = slave.char_class;
                slaveSkillsInput.value = slave.skills || '1,2,3,4';
                slaveTaunterInput.checked = slave.taunter || false;
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
        closeGlobalSettingsModal();
        showToast('Global settings saved successfully.');
    });

    // 6. Form Locking when active
    function setUIStateRunning(isRunning, isPaused = false) {
        btnToggleAddForm.disabled = isRunning;
        btnSaveSettings.disabled = isRunning && !isPaused;
        chkSelectAll.disabled = isRunning;

        const canEditSettings = !isRunning || isPaused;
        followPlayerInput.disabled = !canEditSettings;
        copyWalkInput.disabled = !canEditSettings;
        targetsInput.disabled = !canEditSettings;
        autoZoneSelect.disabled = !canEditSettings;
        newTagInput.disabled = !canEditSettings;
        btnAddTag.disabled = !canEditSettings;
        newMapInput.disabled = !canEditSettings;
        btnAddMap.disabled = !canEditSettings;

        const mapChks = lockedZonesContainer.querySelectorAll('.chk-map');
        mapChks.forEach(c => c.disabled = !canEditSettings);

        const tagRemoves = whitelistTagsContainer.querySelectorAll('.btn-tag-remove');
        tagRemoves.forEach(btn => btn.disabled = !canEditSettings);

        serverSelect.disabled = isRunning;
        roomNumberInput.disabled = isRunning && !isPaused;

        const slaveChks = slaveTableBody.querySelectorAll('.chk-slave');
        slaveChks.forEach(c => c.disabled = isRunning);

        const actionSelects = slaveTableBody.querySelectorAll('.select-action');
        actionSelects.forEach(sel => sel.disabled = isRunning);

        const slaveTable = document.getElementById('slave-table');
        if (slaveTable) {
            if (isRunning) {
                slaveTable.classList.add('running');
            } else {
                slaveTable.classList.remove('running');
            }
        }

        if (isRunning && !isPaused) {
            addSlaveForm.classList.add('hidden');
        }

        if (isRunning) {
            startDurationCounter();
        } else {
            stopDurationCounter();
        }
    }

    let durationInterval = null;
    let durationStartTime = null;

    function startDurationCounter() {
        const counterEl = document.getElementById('duration-counter');
        const valEl = document.getElementById('duration-val');
        if (!counterEl || !valEl) return;

        counterEl.classList.remove('hidden');
        if (!durationStartTime) {
            durationStartTime = Date.now();
        }

        if (!durationInterval) {
            durationInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - durationStartTime) / 1000);
                const hrs = String(Math.floor(elapsed / 3600)).padStart(2, '0');
                const mins = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
                const secs = String(elapsed % 60).padStart(2, '0');
                valEl.innerText = `${hrs}:${mins}:${secs}`;
            }, 1000);
        }
    }

    function stopDurationCounter() {
        if (durationInterval) {
            clearInterval(durationInterval);
            durationInterval = null;
        }
        durationStartTime = null;
        const counterEl = document.getElementById('duration-counter');
        const valEl = document.getElementById('duration-val');
        if (counterEl) counterEl.classList.add('hidden');
        if (valEl) valEl.innerText = "00:00:00";
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
                </svg><span>START</span>
            `;
            if (res.success) {
                btnStart.classList.add('hidden');
                btnStop.classList.remove('hidden');
                btnPause.classList.remove('hidden');
                resetPauseBtnUI();
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
                </svg><span>STOP</span>
            `;
            if (res.success) {
                btnStop.classList.add('hidden');
                btnPause.classList.add('hidden');
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

    function resetPauseBtnUI() {
        isPausedState = false;
        btnPause.className = 'btn btn-warning';
        btnPause.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon" id="pause-btn-icon">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
            </svg>
            <span id="pause-btn-text">Pause</span>
        `;
    }

    if (btnPause) {
        btnPause.addEventListener('click', () => {
            isPausedState = !isPausedState;
            btnPause.disabled = true;
            btnPause.textContent = isPausedState ? 'Resuming...' : 'Pausing...';
            
            window.pywebview.api.toggle_pause_slaves(isPausedState).then(res => {
                btnPause.disabled = false;
                if (res.success) {
                    if (isPausedState) {
                        btnPause.className = 'btn btn-success';
                        btnPause.innerHTML = `
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon" id="pause-btn-icon">
                                <polygon points="5 3 19 12 5 21 5 3"></polygon>
                            </svg>
                            <span id="pause-btn-text">Resume</span>
                        `;
                    } else {
                        resetPauseBtnUI();
                    }
                } else {
                    isPausedState = !isPausedState; // Revert
                    alert(`Error toggling pause: ${res.error}`);
                    resetPauseBtnUI();
                }
            });
        });
    }

    // 8. Polling Telemetry status
    function startStatusPolling() {
        if (statusInterval) clearInterval(statusInterval);

        statusInterval = setInterval(() => {
            if (!window.pywebview || !window.pywebview.api) return;

            window.pywebview.api.get_status().then(statuses => {
                let anyRunning = false;
                let allPaused = true;
                let activeCount = 0;

                globalConfig.slaves.forEach(s => {
                    let status = statuses ? statuses[s.username] : null;
                    if (!status && statuses) {
                        const matchKey = Object.keys(statuses).find(k => k.toLowerCase() === s.username.toLowerCase());
                        if (matchKey) status = statuses[matchKey];
                    }
                    if (status) {
                        updateRowStatus(s.username, status);
                        if (status.running) {
                            anyRunning = true;
                            activeCount++;
                            if (!status.is_paused) {
                                allPaused = false;
                            }
                        }
                    } else {
                        updateRowStatus(s.username, { running: false, is_connected: false });
                    }
                });

                const isCurrentlyPaused = anyRunning && allPaused;

                if (anyRunning) {
                    btnStart.classList.add('hidden');
                    btnStop.classList.remove('hidden');
                    setUIStateRunning(true, isCurrentlyPaused);
                } else {
                    btnStop.classList.add('hidden');
                    btnStart.classList.remove('hidden');
                    setUIStateRunning(false, false);
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
        const tauntChk = row.querySelector('.chk-taunt-toggle');
        const tauntSwitch = tauntChk ? tauntChk.closest('.mini-switch') : null;
        const telBtn = row.querySelector('.btn-action-telemetry');

        if (!status || !status.running) {
            if (telBtn) telBtn.classList.remove('pulse-running');
            if (colMap) colMap.innerHTML = `<span class="text-muted">-</span>`;
            if (colStatus) {
                colStatus.innerHTML = `
                    <span class="status-pill offline">
                        <span class="status-pill-dot"></span>
                        <span class="status-pill-text">Offline</span>
                    </span>
                `;
            }
            if (hpBar) hpBar.style.width = '0%';
            if (mpBar) mpBar.style.width = '0%';
            if (hpTxt) hpTxt.textContent = '0/0';
            if (mpTxt) mpTxt.textContent = '0/0';
            if (recentSkillsEl) {
                recentSkillsEl.innerHTML = '<span class="text-muted cd-placeholder">-</span>';
            }
            if (tauntSwitch) {
                tauntSwitch.classList.remove('taunt-error-highlight', 'taunt-active-highlight');
                tauntSwitch.removeAttribute('title');
            }
            if (tauntChk) {
                tauntChk.disabled = false;
            }
            const scrollQtyEl = document.getElementById(`scroll-qty-${id}`);
            if (scrollQtyEl) {
                scrollQtyEl.style.display = 'none';
            }
            return;
        }

        if (telBtn) {
            if (status.is_connected) {
                telBtn.classList.add('pulse-running');
            } else {
                telBtn.classList.remove('pulse-running');
            }
        }

        if (colMap) {
            colMap.innerHTML = `
                <div class="location-chip" title="Map: ${status.map || 'Unknown'}, Cell: ${status.cell || ''}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="loc-icon">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                        <circle cx="12" cy="10" r="3"></circle>
                    </svg>
                    <span class="loc-map">${status.map || '-'}</span>
                    <span class="loc-cell">${status.cell ? '(' + status.cell + ')' : ''}</span>
                </div>
            `;
        }

        if (colStatus) {
            let statusClass = 'connecting';
            let statusText = 'Connecting';
            if (status.is_dead) {
                statusClass = 'dead';
                statusText = 'Dead';
            } else if (status.is_paused) {
                statusClass = 'paused';
                statusText = 'Paused';
            } else if (status.is_connected) {
                statusClass = 'online';
                statusText = 'Serving';
            }
            colStatus.innerHTML = `
                <span class="status-pill ${statusClass}">
                    <span class="status-pill-dot"></span>
                    <span class="status-pill-text">${statusText}</span>
                </span>
            `;
        }

        if (recentSkillsEl) {
            const cooldowns = status.cooldowns || { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
            let htmlStr = '<div class="cooldowns-grid">';
            for (let i = 0; i <= 5; i++) {
                const cd = cooldowns[i] || 0;
                const isSkill5 = i === 5;
                const isSkill0 = i === 0;
                const extraClass = isSkill5 ? ' skill-5-badge' : (isSkill0 ? ' skill-0-badge' : '');
                const label = isSkill0 ? 'AA' : i;
                if (cd > 0) {
                    htmlStr += `
                        <span class="skill-cd-badge on-cooldown${extraClass}" title="Skill ${label} on cooldown">
                            <span class="skill-idx">${label}</span>
                            <span class="skill-cd-val">${cd.toFixed(1)}s</span>
                        </span>
                    `;
                } else {
                    htmlStr += `
                        <span class="skill-cd-badge ready${extraClass}" title="Skill ${label} ready">
                            <span class="skill-idx">${label}</span>
                            <span class="skill-cd-val">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            </span>
                        </span>
                    `;
                }
            }
            htmlStr += '</div>';
            recentSkillsEl.innerHTML = htmlStr;
        }

        if (tauntChk) {
            tauntChk.disabled = status.running && !status.is_paused;
        }

        if (tauntSwitch) {
            tauntSwitch.classList.remove('taunt-error-highlight', 'taunt-active-highlight');
            if (status.taunt_error) {
                tauntSwitch.classList.add('taunt-error-highlight');
                tauntSwitch.title = "Scroll of Enrage not found in inventory!";
            } else if (status.is_active_taunter) {
                tauntSwitch.classList.add('taunt-active-highlight');
                tauntSwitch.title = "Currently active taunter (casting Scroll of Enrage)";
            } else {
                tauntSwitch.title = "Auto Loop Taunt (Scroll of Enrage)";
            }
        }

        const scrollQtyEl = document.getElementById(`scroll-qty-${id}`);
        if (scrollQtyEl) {
            if (status.running && status.scroll_enrage_qty !== undefined) {
                scrollQtyEl.textContent = `${status.scroll_enrage_qty} SoE`;
                scrollQtyEl.style.display = 'inline-block';
                scrollQtyEl.className = 'scroll-qty-badge ' + (
                    status.scroll_enrage_qty === 0 ? 'qty-empty' :
                    status.scroll_enrage_qty < 10 ? 'qty-low' : 'qty-ok'
                );
            } else {
                scrollQtyEl.style.display = 'none';
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

    if (!isEmbedded) {
        document.querySelectorAll(".theme-dot").forEach(dot => {
            dot.addEventListener("click", () => {
                const selectedTheme = dot.getAttribute("data-theme");
                applyTheme(selectedTheme);
                if (globalConfig) {
                    globalConfig.theme = selectedTheme;
                    updateActiveThemeDot(selectedTheme);
                    window.pywebview.api.save_config(globalConfig);
                }
            });
        });
    }

    // Info bubble click toggle handler
    const titleClick = document.getElementById("app-title-click");
    const infoBubble = document.getElementById("info-bubble");

    const thTauntClick = document.getElementById("th-taunt-click");
    const tauntInfoBubble = document.getElementById("taunt-info-bubble");

    const formTauntClick = document.getElementById("form-taunt-info-click");
    const formTauntBubble = document.getElementById("form-taunt-info-bubble");

    if (titleClick && infoBubble) {
        titleClick.addEventListener("click", (e) => {
            e.stopPropagation();
            infoBubble.classList.toggle("show");
            if (tauntInfoBubble) tauntInfoBubble.classList.remove("show");
            if (formTauntBubble) formTauntBubble.classList.remove("show");
        });
        infoBubble.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }

    if (thTauntClick && tauntInfoBubble) {
        thTauntClick.addEventListener("click", (e) => {
            e.stopPropagation();
            tauntInfoBubble.classList.toggle("show");
            if (infoBubble) infoBubble.classList.remove("show");
            if (formTauntBubble) formTauntBubble.classList.remove("show");
        });
        tauntInfoBubble.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }

    if (formTauntClick && formTauntBubble) {
        formTauntClick.addEventListener("click", (e) => {
            e.stopPropagation();
            formTauntBubble.classList.toggle("show");
            if (infoBubble) infoBubble.classList.remove("show");
            if (tauntInfoBubble) tauntInfoBubble.classList.remove("show");
        });
        formTauntBubble.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }

    document.addEventListener("click", () => {
        if (infoBubble) infoBubble.classList.remove("show");
        if (tauntInfoBubble) tauntInfoBubble.classList.remove("show");
        if (formTauntBubble) formTauntBubble.classList.remove("show");
    });

    // ==========================================
    // 9. PLAYER TELEMETRY MODAL CONTROLLER
    // ==========================================
    const modalPlayerTelemetry = document.getElementById('modal-player-telemetry');
    const btnCloseTelemetryModal = document.getElementById('btn-close-telemetry-modal');
    const btnCloseTelemetryModalFt = document.getElementById('btn-close-telemetry-modal-ft');
    const telSelectAccount = document.getElementById('tel-select-account');

    const telModalUsername = document.getElementById('tel-modal-username');
    const telModalClass = document.getElementById('tel-modal-class');
    const telModalStatusPill = document.getElementById('tel-modal-status-pill');
    const telModalStatusText = document.getElementById('tel-modal-status-text');
    const telModalCombatPill = document.getElementById('tel-modal-combat-pill');

    const telHpBar = document.getElementById('tel-hp-bar');
    const telHpVal = document.getElementById('tel-hp-val');
    const telMpBar = document.getElementById('tel-mp-bar');
    const telMpVal = document.getElementById('tel-mp-val');

    const telLocVal = document.getElementById('tel-loc-val');
    const telCellPadVal = document.getElementById('tel-cell-pad-val');
    const telCoordsVal = document.getElementById('tel-coords-val');
    const telServerVal = document.getElementById('tel-server-val');
    const telGoldVal = document.getElementById('tel-gold-val');
    const telFarmedGoldVal = document.getElementById('tel-farmed-gold-val');
    const telFarmedExpVal = document.getElementById('tel-farmed-exp-val');
    const telCdRedVal = document.getElementById('tel-cd-red-val');

    const telTargetEmpty = document.getElementById('tel-target-empty');
    const telTargetContent = document.getElementById('tel-target-content');
    const telTargetName = document.getElementById('tel-target-name');
    const telTargetMapId = document.getElementById('tel-target-mapid');
    const telTargetHpBar = document.getElementById('tel-target-hp-bar');
    const telTargetHpVal = document.getElementById('tel-target-hp-val');
    const telTargetAuras = document.getElementById('tel-target-auras');

    const telAurasCount = document.getElementById('tel-auras-count');
    const telAurasList = document.getElementById('tel-auras-list');
    const telAurasEmpty = document.getElementById('tel-auras-empty');

    const telDropsCount = document.getElementById('tel-drops-count');
    const telDropsSummary = document.getElementById('tel-drops-summary');
    const telDropsTbody = document.getElementById('tel-drops-tbody');
    const telDropsEmpty = document.getElementById('tel-drops-empty');

    let currentTelemetryUsername = null;
    let telemetryInterval = null;

    // Telemetry Modal Tabs Navigation
    const modalTelemetryTabs = document.querySelectorAll('#modal-player-telemetry .modal-tab');
    const modalTelemetryContents = document.querySelectorAll('#modal-player-telemetry .modal-tab-content');

    modalTelemetryTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            modalTelemetryTabs.forEach(t => t.classList.remove('active'));
            modalTelemetryContents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const targetId = tab.getAttribute('data-tab');
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add('active');
        });
    });

    function openTelemetryModal(username) {
        if (modalPlayerTelemetry) {
            modalPlayerTelemetry.classList.remove('hidden');
        }

        const slaves = (globalConfig && Array.isArray(globalConfig.slaves)) ? globalConfig.slaves : [];
        if (!username && slaves.length > 0 && slaves[0].username) {
            username = slaves[0].username;
        }
        currentTelemetryUsername = username || '';

        // Populate accounts selector
        if (telSelectAccount) {
            telSelectAccount.innerHTML = '';
            slaves.forEach(s => {
                if (!s || !s.username) return;
                const opt = document.createElement('option');
                opt.value = s.username;
                opt.textContent = `${s.username} (${s.char_class || 'Class'})`;
                if (currentTelemetryUsername && s.username.toLowerCase() === currentTelemetryUsername.toLowerCase()) {
                    opt.selected = true;
                }
                telSelectAccount.appendChild(opt);
            });
        }

        // Set initial header info immediately
        if (telModalUsername) {
            telModalUsername.textContent = currentTelemetryUsername || 'Slave Account';
        }
        const currentSlave = slaves.find(s => s && (s.username || '').toLowerCase() === (currentTelemetryUsername || '').toLowerCase());
        if (telModalClass) {
            telModalClass.textContent = currentSlave ? (currentSlave.char_class || '-') : '-';
        }
        if (telModalStatusPill && telModalStatusText) {
            telModalStatusPill.className = 'status-pill offline';
            telModalStatusText.textContent = 'Offline';
        }

        startTelemetryModalPolling();
    }
    window.openTelemetryModal = openTelemetryModal;

    function closeTelemetryModal() {
        if (modalPlayerTelemetry) {
            modalPlayerTelemetry.classList.add('hidden');
        }
        stopTelemetryModalPolling();
    }
    window.closeTelemetryModal = closeTelemetryModal;

    if (btnCloseTelemetryModal) {
        btnCloseTelemetryModal.addEventListener('click', closeTelemetryModal);
    }
    if (btnCloseTelemetryModalFt) {
        btnCloseTelemetryModalFt.addEventListener('click', closeTelemetryModal);
    }
    if (modalPlayerTelemetry) {
        modalPlayerTelemetry.addEventListener('click', (e) => {
            if (e.target === modalPlayerTelemetry) {
                closeTelemetryModal();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalPlayerTelemetry && !modalPlayerTelemetry.classList.contains('hidden')) {
            closeTelemetryModal();
        }
    });

    if (telSelectAccount) {
        telSelectAccount.addEventListener('change', () => {
            currentTelemetryUsername = telSelectAccount.value;
            pollTelemetryDetails();
        });
    }

    function startTelemetryModalPolling() {
        stopTelemetryModalPolling();
        pollTelemetryDetails();
        telemetryInterval = setInterval(pollTelemetryDetails, 1000);
    }

    function stopTelemetryModalPolling() {
        if (telemetryInterval) {
            clearInterval(telemetryInterval);
            telemetryInterval = null;
        }
    }

    function pollTelemetryDetails() {
        if (!currentTelemetryUsername) return;
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_telemetry) {
            window.pywebview.api.get_telemetry(currentTelemetryUsername).then(data => {
                renderTelemetryData(data);
            }).catch(err => {
                console.error("Telemetry fetch error:", err);
            });
        } else {
            const slaves = (globalConfig && Array.isArray(globalConfig.slaves)) ? globalConfig.slaves : [];
            const currentSlave = slaves.find(s => s && (s.username || '').toLowerCase() === (currentTelemetryUsername || '').toLowerCase());
            renderTelemetryData({
                username: currentTelemetryUsername,
                char_class: currentSlave ? (currentSlave.char_class || '-') : '-',
                running: false,
                is_connected: false,
                hp: 0,
                max_hp: 0,
                mp: 0,
                max_mp: 0,
                map: '-',
                cell: '-',
                pad: '-',
                x: 0,
                y: 0,
                gold: 0,
                gold_farmed: 0,
                exp_farmed: 0,
                cd_reduction: 0,
                target: null,
                auras: [],
                dropped_items: []
            });
        }
    }

    function renderTelemetryData(data) {
        if (!data) return;

        // 1. Header
        if (telModalUsername) telModalUsername.textContent = data.username || currentTelemetryUsername;
        if (telModalClass) telModalClass.textContent = data.char_class || '-';

        if (telModalStatusPill && telModalStatusText) {
            telModalStatusPill.className = 'status-pill';
            if (data.running) {
                if (data.is_dead) {
                    telModalStatusPill.classList.add('dead');
                    telModalStatusText.textContent = 'Dead';
                } else if (data.is_paused) {
                    telModalStatusPill.classList.add('paused');
                    telModalStatusText.textContent = 'Paused';
                } else if (data.is_connected) {
                    telModalStatusPill.classList.add('online');
                    telModalStatusText.textContent = 'Serving';
                } else {
                    telModalStatusPill.classList.add('connecting');
                    telModalStatusText.textContent = 'Connecting...';
                }
            } else {
                telModalStatusPill.classList.add('offline');
                telModalStatusText.textContent = 'Offline';
            }
        }

        if (telModalCombatPill) {
            if (data.is_in_combat) {
                telModalCombatPill.className = 'tel-combat-pill combat';
                telModalCombatPill.textContent = 'IN COMBAT';
            } else {
                telModalCombatPill.className = 'tel-combat-pill';
                telModalCombatPill.textContent = 'PEACEFUL / IDLE';
            }
        }

        // 2. Vitals & Stats
        const hp = data.hp || 0;
        const maxHp = data.max_hp || 0;
        const hpPct = maxHp > 0 ? Math.min(100, Math.max(0, (hp / maxHp) * 100)) : 0;
        if (telHpBar) telHpBar.style.width = `${hpPct}%`;
        if (telHpVal) telHpVal.textContent = `${hp} / ${maxHp} (${Math.round(hpPct)}%)`;

        const mp = data.mp || 0;
        const maxMp = data.max_mp || 0;
        const mpPct = maxMp > 0 ? Math.min(100, Math.max(0, (mp / maxMp) * 100)) : 0;
        if (telMpBar) telMpBar.style.width = `${mpPct}%`;
        if (telMpVal) telMpVal.textContent = `${mp} / ${maxMp} (${Math.round(mpPct)}%)`;

        if (telLocVal) telLocVal.textContent = data.map || '-';
        if (telCellPadVal) telCellPadVal.textContent = `${data.cell || '-'} / ${data.pad || '-'}`;
        if (telCoordsVal) telCoordsVal.textContent = `X: ${data.x || 0}, Y: ${data.y || 0}`;
        if (telServerVal) telServerVal.textContent = data.server || '-';
        if (telGoldVal) telGoldVal.textContent = (data.gold || 0).toLocaleString();
        if (telFarmedGoldVal) telFarmedGoldVal.textContent = `+${(data.gold_farmed || 0).toLocaleString()}`;
        if (telFarmedExpVal) telFarmedExpVal.textContent = `+${(data.exp_farmed || 0).toLocaleString()}`;
        if (telCdRedVal) telCdRedVal.textContent = `${Math.round((data.cd_reduction || 0) * 100)}%`;

        // 3. Combat Target
        if (data.target && data.target.name) {
            if (telTargetEmpty) telTargetEmpty.classList.add('hidden');
            if (telTargetContent) telTargetContent.classList.remove('hidden');
            if (telTargetName) telTargetName.textContent = data.target.name;
            if (telTargetMapId) telTargetMapId.textContent = `MonMapID: ${data.target.map_id}`;

            const tHp = data.target.hp || 0;
            const tMaxHp = data.target.max_hp || 0;
            const tPct = tMaxHp > 0 ? Math.min(100, Math.max(0, (tHp / tMaxHp) * 100)) : 0;
            if (telTargetHpBar) telTargetHpBar.style.width = `${tPct}%`;
            if (telTargetHpVal) telTargetHpVal.textContent = `${tHp} / ${tMaxHp} (${Math.round(tPct)}%)`;

            if (telTargetAuras) {
                if (data.target.auras && data.target.auras.length > 0) {
                    telTargetAuras.innerHTML = data.target.auras.map(a => 
                        `<span class="target-aura-chip">${a.name}${a.stacks > 1 ? ' x' + a.stacks : ''} (${a.remaining}s)</span>`
                    ).join('');
                } else {
                    telTargetAuras.innerHTML = `<span class="text-muted" style="font-size: 0.72rem;">No target debuffs</span>`;
                }
            }
        } else {
            if (telTargetEmpty) telTargetEmpty.classList.remove('hidden');
            if (telTargetContent) telTargetContent.classList.add('hidden');
        }

        // 4. Active Auras
        const auras = data.auras || [];
        if (telAurasCount) telAurasCount.textContent = auras.length;
        if (auras.length > 0) {
            if (telAurasEmpty) telAurasEmpty.classList.add('hidden');
            if (telAurasList) {
                telAurasList.innerHTML = auras.map(a => {
                    const isBuff = (a.type || 'buff').toLowerCase() === 'buff';
                    const typeClass = isBuff ? 'buff' : 'debuff';
                    const typeLabel = isBuff ? 'Buff' : 'Debuff';
                    const timerStr = a.remaining > 0 ? `${a.remaining}s remaining` : 'Active';
                    return `
                        <div class="aura-card ${typeClass}">
                            <div class="aura-header-row">
                                <span class="aura-name">${a.name}</span>
                                ${a.stacks > 1 ? `<span class="aura-stacks">x${a.stacks}</span>` : ''}
                            </div>
                            <div class="aura-details-row">
                                <span class="aura-type-tag">${typeLabel}</span>
                                <span class="aura-timer">${timerStr}</span>
                            </div>
                            ${a.spell ? `<div style="font-size: 0.68rem; color: var(--text-secondary); margin-top: 2px;">From: ${a.spell}</div>` : ''}
                        </div>
                    `;
                }).join('');
            }
        } else {
            if (telAurasList) telAurasList.innerHTML = '';
            if (telAurasEmpty) telAurasEmpty.classList.remove('hidden');
        }

        // 5. Dropped Items
        const drops = data.dropped_items || [];
        if (telDropsCount) telDropsCount.textContent = drops.length;
        if (telDropsSummary) telDropsSummary.textContent = `${drops.length} item drop(s) recorded in session`;

        if (drops.length > 0) {
            if (telDropsEmpty) telDropsEmpty.classList.add('hidden');
            if (telDropsTbody) {
                telDropsTbody.innerHTML = drops.map(d => {
                    const acTag = d.is_acs ? '<span class="badge-ac">AC</span>' : '';
                    const tempTag = d.is_temp ? '<span class="badge-temp">TEMP</span>' : '';
                    const isLooted = d.picked_up;
                    const statusBadge = isLooted 
                        ? '<span class="drop-status-badge looted">Looted</span>' 
                        : '<span class="drop-status-badge on-ground">On Ground</span>';
                    const actionBtn = isLooted 
                        ? '<span class="text-muted" style="font-size: 0.72rem;">Done</span>' 
                        : `<button class="btn-pickup-drop" data-id="${d.item_id}" data-name="${d.item_name}">Pick Up</button>`;
                    return `
                        <tr>
                            <td>
                                <div class="drop-item-name-cell">
                                    <span>${d.item_name}</span>
                                    ${acTag}
                                    ${tempTag}
                                </div>
                            </td>
                            <td>${d.qty || 1}</td>
                            <td><span class="text-muted">${d.s_type || 'Item'}</span></td>
                            <td><span class="text-muted" style="font-family: monospace;">${d.time || '-'}</span></td>
                            <td>${statusBadge}</td>
                            <td style="text-align: center;">${actionBtn}</td>
                        </tr>
                    `;
                }).join('');
            }
        } else {
            if (telDropsTbody) telDropsTbody.innerHTML = '';
            if (telDropsEmpty) telDropsEmpty.classList.remove('hidden');
        }
    }

    // Pick Up Item Click Event Delegation
    if (telDropsTbody) {
        telDropsTbody.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-pickup-drop');
            if (btn) {
                const itemId = btn.getAttribute('data-id');
                const itemName = btn.getAttribute('data-name');
                btn.disabled = true;
                btn.textContent = 'Picking...';
                if (window.pywebview && window.pywebview.api && window.pywebview.api.pickup_drop) {
                    window.pywebview.api.pickup_drop(currentTelemetryUsername, itemId).then(res => {
                        if (res && res.success) {
                            showToast(`Picked up drop: ${itemName}`);
                            pollTelemetryDetails();
                        } else {
                            showToast(res && res.error ? res.error : 'Failed to pick up item', true);
                            btn.disabled = false;
                            btn.textContent = 'Pick Up';
                        }
                    }).catch(err => {
                        showToast('Error picking up item', true);
                        btn.disabled = false;
                        btn.textContent = 'Pick Up';
                    });
                }
            }
        });
    }
});
