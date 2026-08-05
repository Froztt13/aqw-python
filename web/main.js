document.addEventListener('DOMContentLoaded', () => {
    // Whitelist tags list
    let whitelistItems = [];
    let statusInterval = null;
    let selectedScript = null;

    // Elements
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const tabTitle = document.getElementById('tab-title');
    const tabSubtitle = document.getElementById('tab-subtitle');
    
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnGotoLogs = document.getElementById('btn-goto-logs');
    
    const connIndicator = document.getElementById('connection-indicator');
    const connText = document.getElementById('connection-text');
    
    // Inputs
    const usernameInput = document.getElementById('input-username');
    const passwordInput = document.getElementById('input-password');
    const serverSelect = document.getElementById('select-server');
    const roomInput = document.getElementById('input-room');
    
    const inputScriptPath = document.getElementById('input-script-path');
    const btnSelectScript = document.getElementById('btn-select-script');
    
    const farmClassInput = document.getElementById('input-farm-class');
    const soloClassInput = document.getElementById('input-solo-class');
    
    // Whitelist Elements
    const whitelistTagsContainer = document.getElementById('whitelist-tags');
    const newTagInput = document.getElementById('input-new-tag');
    const btnAddTag = document.getElementById('btn-add-tag');
    const presetButtons = document.querySelectorAll('.btn-preset');
    
    // Settings switches
    const chkAutoRelogin = document.getElementById('chk-auto-relogin');
    const chkAntiMod = document.getElementById('chk-anti-mod');
    const chkMuteSpam = document.getElementById('chk-mute-spam');
    const chkShowChat = document.getElementById('chk-show-chat');
    
    const btnSaveSettings = document.getElementById('btn-save-settings');
    const btnResetSettings = document.getElementById('btn-reset-settings');
    const btnTogglePassword = document.getElementById('btn-toggle-password');

    // Dashboard values
    const valHpProgress = document.getElementById('hp-progress');
    const valHpValues = document.getElementById('hp-values');
    const valMpProgress = document.getElementById('mp-progress');
    const valMpValues = document.getElementById('mp-values');
    const valMap = document.getElementById('val-map');
    const valCellPad = document.getElementById('val-cell-pad');
    const valState = document.getElementById('val-state');
    
    const valGold = document.getElementById('val-gold');
    const valGoldFarmed = document.getElementById('val-gold-farmed');
    const valExpFarmed = document.getElementById('val-exp-farmed');
    const valCmdIndex = document.getElementById('val-cmd-index');
    
    const valInventoryCount = document.getElementById('val-inventory-count');
    const valBankCount = document.getElementById('val-bank-count');
    
    // Console Logs
    const consoleViewport = document.getElementById('console-viewport');
    const miniConsole = document.getElementById('mini-console');
    const logFilterInput = document.getElementById('input-log-filter');
    const btnClearLogs = document.getElementById('btn-clear-logs');
    const chkAutoScroll = document.getElementById('chk-auto-scroll');

    // Tab Information configuration
    const tabInfo = {
        'dashboard': {
            title: 'Player Stats',
            subtitle: 'Real-time character statistics and combat status'
        },
        'script': {
            title: 'Script & Account',
            subtitle: 'Set up credentials, target map scripts, and class setups'
        },
        'settings': {
            title: 'Bot Toggles',
            subtitle: 'Manage client notifications, relogging timers, and moderator protection'
        },
        'logs': {
            title: 'Live Terminal Console',
            subtitle: 'Raw diagnostic console outputs directly from the running Python bot'
        }
    };

    // 1. Navigation Controller
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            navButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
            
            // Update Title
            if (tabInfo[targetTab]) {
                tabTitle.textContent = tabInfo[targetTab].title;
                tabSubtitle.textContent = tabInfo[targetTab].subtitle;
            }
        });
    });

    btnGotoLogs.addEventListener('click', () => {
        const logsBtn = document.querySelector('[data-tab="logs"]');
        if (logsBtn) logsBtn.click();
    });

    // Toggle Password Visibility
    btnTogglePassword.addEventListener('click', () => {
        const isPassword = passwordInput.getAttribute('type') === 'password';
        passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
        btnTogglePassword.style.color = isPassword ? 'var(--primary-color)' : 'var(--text-secondary)';
    });

    // 2. Log Stream Receiver
    window.addLog = function(htmlMsg) {
        if (!htmlMsg) return;
        
        // Append to main console
        const mainLine = document.createElement('div');
        mainLine.className = 'log-line';
        mainLine.innerHTML = htmlMsg;
        consoleViewport.appendChild(mainLine);

        // Append to dashboard summary mini console
        const miniLine = document.createElement('div');
        miniLine.className = 'log-line';
        miniLine.innerHTML = htmlMsg;
        miniConsole.appendChild(miniLine);

        // Keep viewports clean (max 500 lines to avoid slow rendering)
        while (consoleViewport.childNodes.length > 500) {
            consoleViewport.removeChild(consoleViewport.firstChild);
        }
        while (miniConsole.childNodes.length > 30) {
            miniConsole.removeChild(miniConsole.firstChild);
        }

        // Apply filter on the new line if log filter is active
        applyFilterToLine(mainLine);

        // Scroll to bottom if auto-scroll checked
        if (chkAutoScroll.checked) {
            consoleViewport.scrollTop = consoleViewport.scrollHeight;
            miniConsole.scrollTop = miniConsole.scrollHeight;
        }
    };

    btnClearLogs.addEventListener('click', () => {
        consoleViewport.innerHTML = '<div class="log-line text-muted">Console logs cleared.</div>';
        miniConsole.innerHTML = '<div class="log-line text-muted">Console logs cleared.</div>';
    });

    // Search filter for logs
    logFilterInput.addEventListener('input', () => {
        const filterText = logFilterInput.value.toLowerCase();
        const lines = consoleViewport.querySelectorAll('.log-line');
        lines.forEach(line => {
            if (line.textContent.toLowerCase().includes(filterText)) {
                line.style.display = 'block';
            } else {
                line.style.display = 'none';
            }
        });
    });

    function applyFilterToLine(line) {
        const filterText = logFilterInput.value.toLowerCase();
        if (filterText && !line.textContent.toLowerCase().includes(filterText)) {
            line.style.display = 'none';
        }
    }

    // 3. Whitelist Tag Manager Controller
    function renderTags() {
        whitelistTagsContainer.innerHTML = '';
        const isRunning = btnStart.classList.contains('hidden');
        whitelistItems.forEach((item, index) => {
            const tagEl = document.createElement('span');
            tagEl.className = 'tag';
            tagEl.innerHTML = `${item} <button class="btn-tag-remove" data-index="${index}" ${isRunning ? 'disabled' : ''}>&times;</button>`;
            whitelistTagsContainer.appendChild(tagEl);
        });

        // Update presets active states
        presetButtons.forEach(btn => {
            const item = btn.getAttribute('data-item');
            if (whitelistItems.includes(item)) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    whitelistTagsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-tag-remove')) {
            const index = parseInt(e.target.getAttribute('data-index'));
            whitelistItems.splice(index, 1);
            renderTags();
        }
    });

    function addCustomTag() {
        const val = newTagInput.value.trim();
        if (val && !whitelistItems.includes(val)) {
            whitelistItems.push(val);
            renderTags();
            newTagInput.value = '';
        }
    }

    btnAddTag.addEventListener('click', addCustomTag);
    newTagInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addCustomTag();
        }
    });

    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.getAttribute('data-item');
            const idx = whitelistItems.indexOf(item);
            if (idx === -1) {
                whitelistItems.push(item);
            } else {
                whitelistItems.splice(idx, 1);
            }
            renderTags();
        });
    });

    // File selection handler
    btnSelectScript.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.select_script().then(result => {
                if (result) {
                    selectedScript = result;
                    inputScriptPath.value = selectedScript.display_name;
                }
            });
        }
    });

    // 4. PyWebview Integration Hooks
    function checkPythonAPI() {
        if (window.pywebview && window.pywebview.api) {
            initApp();
        } else {
            setTimeout(checkPythonAPI, 100);
        }
    }

    checkPythonAPI();

    function initApp() {
        // Load settings and start polling status
        loadUserConfig();
        startStatusPolling();
    }

    function loadUserConfig() {
        window.pywebview.api.load_config().then(config => {
            if (!config) return;
            usernameInput.value = config.username || '';
            passwordInput.value = config.password || '';
            serverSelect.value = config.server || 'Artix';
            roomInput.value = config.room_number || '1';
            
            selectedScript = config.selected_script || null;
            if (selectedScript) {
                inputScriptPath.value = selectedScript.display_name || selectedScript.path || '';
            } else {
                // Fallback for old configs that stored just path
                if (config.bot_path) {
                    selectedScript = {
                        display_name: config.bot_display_name || config.bot_path.split('.').pop() + '.py',
                        path: config.bot_path,
                        abs_path: config.bot_abs_path || '',
                        external: !!config.bot_external,
                        parent_dir: config.bot_parent_dir || ''
                    };
                    inputScriptPath.value = selectedScript.display_name;
                } else {
                    inputScriptPath.value = '';
                }
            }

            farmClassInput.value = config.farm_class || '';
            soloClassInput.value = config.solo_class || '';
            
            chkAutoRelogin.checked = config.auto_relogin !== false;
            chkAntiMod.checked = config.anti_mod !== false;
            chkMuteSpam.checked = config.mute_spam !== false;
            chkShowChat.checked = config.show_chat !== false;

            whitelistItems = config.whitelist || [];
            renderTags();
        });
    }

    function compileConfig() {
        return {
            username: usernameInput.value.trim(),
            password: passwordInput.value,
            server: serverSelect.value,
            room_number: parseInt(roomInput.value) || 1,
            
            bot_path: selectedScript ? selectedScript.path : '',
            bot_display_name: selectedScript ? selectedScript.display_name : '',
            bot_abs_path: selectedScript ? selectedScript.abs_path : '',
            bot_external: selectedScript ? !!selectedScript.external : false,
            bot_parent_dir: selectedScript ? selectedScript.parent_dir : '',
            selected_script: selectedScript,
            
            farm_class: farmClassInput.value.trim(),
            solo_class: soloClassInput.value.trim(),
            whitelist: whitelistItems,
            auto_relogin: chkAutoRelogin.checked,
            anti_mod: chkAntiMod.checked,
            mute_spam: chkMuteSpam.checked,
            show_chat: chkShowChat.checked
        };
    }

    btnSaveSettings.addEventListener('click', () => {
        const payload = compileConfig();
        window.pywebview.api.save_config(payload).then(res => {
            if (res.success) {
                alert('Configuration saved successfully.');
            } else {
                alert(`Error saving configuration: ${res.error}`);
            }
        });
    });

    btnResetSettings.addEventListener('click', () => {
        if (confirm('Are you sure you want to restore default settings?')) {
            whitelistItems = [
                "Gem of Nulgath",
                "Diamond of Nulgath",
                "Voucher of Nulgath (non-mem)",
                "Tainted Gem",
                "Dark Crystal Shard"
            ];
            usernameInput.value = '';
            passwordInput.value = '';
            serverSelect.value = 'Artix';
            roomInput.value = '1';
            selectedScript = null;
            inputScriptPath.value = '';
            farmClassInput.value = '';
            soloClassInput.value = '';
            chkAutoRelogin.checked = true;
            chkAntiMod.checked = true;
            chkMuteSpam.checked = true;
            chkShowChat.checked = true;
            renderTags();
        }
    });

    // 5. Bot Runner Control Hooks
    btnStart.addEventListener('click', () => {
        const config = compileConfig();
        
        if (!config.username || !config.password) {
            alert('Username and Password are required to start the bot!');
            document.querySelector('[data-tab="script"]').click();
            return;
        }

        if (!config.bot_path) {
            alert('Please select a bot script file first!');
            document.querySelector('[data-tab="script"]').click();
            return;
        }

        btnStart.disabled = true;
        btnStart.textContent = 'Launching...';
        
        connIndicator.className = 'status-indicator connecting';
        connText.textContent = 'Connecting...';

        window.pywebview.api.start_bot(config).then(res => {
            if (res.success) {
                btnStart.classList.add('hidden');
                btnStop.classList.remove('hidden');
                btnStart.disabled = false;
                btnStart.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg> Start Bot
                `;
                setTimeout(() => {
                    const logsBtn = document.querySelector('[data-tab="logs"]');
                    if (logsBtn) logsBtn.click();
                }, 800);
            } else {
                btnStart.disabled = false;
                btnStart.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg> Start Bot
                `;
                alert(`Failed to start bot: ${res.error}`);
                connIndicator.className = 'status-indicator disconnected';
                connText.textContent = 'Disconnected';
            }
        });
    });

    btnStop.addEventListener('click', () => {
        btnStop.disabled = true;
        btnStop.textContent = 'Stopping...';
        window.pywebview.api.stop_bot().then(res => {
            btnStop.disabled = false;
            btnStop.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                    <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
                </svg> Stop Bot
            `;
            if (res.success) {
                btnStop.classList.add('hidden');
                btnStart.classList.remove('hidden');
                connIndicator.className = 'status-indicator disconnected';
                connText.textContent = 'Disconnected';
            } else {
                alert(`Error stopping bot: ${res.error}`);
            }
        });
    });

    // 6. Polling Status Loop
    function startStatusPolling() {
        if (statusInterval) clearInterval(statusInterval);
        
        statusInterval = setInterval(() => {
            if (!window.pywebview || !window.pywebview.api) return;

            window.pywebview.api.get_status().then(status => {
                updateDashboard(status);
            }).catch(err => {
                console.error("Status check failed", err);
            });
        }, 1000);
    }

    function setBotRunningUIState(isRunning) {
        const navDashboard = document.getElementById('nav-dashboard');
        if (!navDashboard) return;

        if (isRunning) {
            navDashboard.classList.remove('hidden');
        } else {
            navDashboard.classList.add('hidden');
            // If the active tab was dashboard (Player Stats), switch back to script tab
            const activeBtn = document.querySelector('.nav-btn.active');
            if (activeBtn && activeBtn.getAttribute('data-tab') === 'dashboard') {
                const scriptBtn = document.querySelector('[data-tab="script"]');
                if (scriptBtn) scriptBtn.click();
            }
        }

        // Disable/Enable all controls inside Script & Account tab
        const scriptTab = document.getElementById('tab-script');
        if (scriptTab) {
            const inputs = scriptTab.querySelectorAll('input, select, button');
            inputs.forEach(el => {
                el.disabled = isRunning;
            });
        }
        
        // Also disable preset tags
        const presetBtns = document.querySelectorAll('.btn-preset');
        presetBtns.forEach(btn => {
            btn.disabled = isRunning;
        });
    }

    function updateDashboard(status) {
        if (!status || !status.running) {
            setBotRunningUIState(false);
            btnStop.classList.add('hidden');
            btnStart.classList.remove('hidden');
            connIndicator.className = 'status-indicator disconnected';
            connText.textContent = 'Disconnected';
            
            valHpProgress.style.width = '0%';
            valHpValues.textContent = '0 / 0';
            valMpProgress.style.width = '0%';
            valMpValues.textContent = '0 / 0';
            valMap.textContent = '-';
            valCellPad.textContent = '-';
            valState.textContent = 'Stopped';
            valState.className = 'value';
            
            valGoldFarmed.textContent = '0';
            valExpFarmed.textContent = '0';
            valCmdIndex.textContent = '0';
            
            valInventoryCount.textContent = '0';
            valBankCount.textContent = '0';
            valGold.textContent = '0';
            return;
        }

        setBotRunningUIState(true);
        btnStart.classList.add('hidden');
        btnStop.classList.remove('hidden');

        if (status.is_connected) {
            connIndicator.className = 'status-indicator connected';
            connText.textContent = 'Connected';
        } else {
            connIndicator.className = 'status-indicator connecting';
            connText.textContent = 'Connecting...';
        }

        const hpPercent = status.max_hp > 0 ? (status.hp / status.max_hp) * 100 : 0;
        valHpProgress.style.width = `${Math.min(100, Math.max(0, hpPercent))}%`;
        valHpValues.textContent = `${status.hp} / ${status.max_hp}`;

        const mpPercent = status.max_mp > 0 ? (status.mp / status.max_mp) * 100 : 0;
        valMpProgress.style.width = `${Math.min(100, Math.max(0, mpPercent))}%`;
        valMpValues.textContent = `${status.mp} / ${status.max_mp}`;

        valMap.textContent = status.cell !== "Unknown" ? `Map / Room ${roomInput.value}` : '-';
        valCellPad.textContent = `${status.cell} (${status.pad})`;

        if (status.is_dead) {
            valState.textContent = 'DEAD';
            valState.className = 'value log-red log-bold';
        } else if (status.in_combat) {
            valState.textContent = 'IN COMBAT';
            valState.className = 'value log-yellow log-bold';
        } else if (status.is_connected) {
            valState.textContent = 'FARMING';
            valState.className = 'value log-green log-bold';
        } else {
            valState.textContent = 'CONNECTING';
            valState.className = 'value text-muted';
        }

        valGoldFarmed.textContent = status.gold_farmed.toLocaleString();
        valExpFarmed.textContent = status.exp_farmed.toLocaleString();
        valCmdIndex.textContent = status.index;

        valInventoryCount.textContent = status.inventory_count;
        valBankCount.textContent = status.bank_count;
        valGold.textContent = status.gold.toLocaleString();
    }
});
