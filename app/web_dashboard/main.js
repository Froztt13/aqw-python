document.addEventListener('DOMContentLoaded', () => {
    let statusInterval = null;
    let currentTheme = localStorage.getItem("global-theme") || "default";

    function formatTimeRunning(seconds) {
        if (!seconds) return "00:00:00";
        const hrs = String(Math.floor(seconds / 3600)).padStart(2, '0');
        const mins = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
        const secs = String(seconds % 60).padStart(2, '0');
        return `${hrs}:${mins}:${secs}`;
    }

    // DOM Elements
    const sysCpu = document.getElementById('sys-cpu');
    const sysMem = document.getElementById('sys-mem');
    const pingIndicator = document.getElementById('ping-indicator');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const bannerDot = document.querySelector('.banner-glow-dot');
    const bannerDescription = document.getElementById('banner-description');

    // Sidebar & Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const cardNavButtons = document.querySelectorAll('.btn-navigate');

    // Bot Cards, Badges, Details
    const cards = {
        aqw: document.getElementById('card-aqw'),
        slavery: document.getElementById('card-slavery'),
        temple: document.getElementById('card-temple'),
        eclipse: document.getElementById('card-eclipse')
    };

    const badges = {
        aqw: document.getElementById('status-aqw'),
        slavery: document.getElementById('status-slavery'),
        temple: document.getElementById('status-temple'),
        eclipse: document.getElementById('status-eclipse')
    };

    const details = {
        aqw: document.getElementById('details-aqw'),
        slavery: document.getElementById('details-slavery'),
        temple: document.getElementById('details-temple'),
        eclipse: document.getElementById('details-eclipse')
    };

    // Tab Pane Titles and Subtitles Mapping
    const tabDetails = {
        dashboard: {
            title: "Dashboard Overview",
            subtitle: "Real-time overview and statistics of all active bots"
        },
        aqw: {
            title: "AQW Solo Bot Client",
            subtitle: "Load custom python scripts, set whitelists, and farm single-player maps"
        },
        slavery: {
            title: "Slavery Bot Army",
            subtitle: "Command and coordinate multiple character sessions under a follower master"
        },
        temple: {
            title: "Temple Shrine Bot",
            subtitle: "Automate Solstice Moon and Midnight Sun boss rooms using multi-role party templates"
        },
        eclipse: {
            title: "Maid Eclipse Client",
            subtitle: "Advanced 4-player coordination bot specifically built for defeating the Eclipse Shrine"
        }
    };

    // --- Tab Switching Logic ---
    function switchTab(tabId) {
        // 1. Update navigation items
        navItems.forEach(item => {
            if (item.getAttribute('data-tab') === tabId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // 2. Update visible pane
        tabPanes.forEach(pane => {
            if (pane.id === `pane-${tabId}`) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        // 3. Update Title & Subtitle in topbar
        if (tabDetails[tabId]) {
            pageTitle.textContent = tabDetails[tabId].title;
            pageSubtitle.textContent = tabDetails[tabId].subtitle;
        }

        // 4. Lazy Load Iframes
        if (tabId !== 'dashboard') {
            const iframe = document.getElementById(`iframe-${tabId}`);
            if (iframe && iframe.src === 'about:blank') {
                console.log(`Lazy loading iframe for: ${tabId}`);
                iframe.src = `/${tabId}/`;
                iframe.onload = () => {
                    applyThemeToIframe(iframe, currentTheme);
                };
            }
        }
    }

    // Event listeners for Sidebar menu items
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Event listeners for "Configure Bot" buttons inside Dashboard cards
    cardNavButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            switchTab(targetId);
        });
    });

    // --- PyWebview Hook ---
    function checkPythonAPI() {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_hub_status) {
            initApp();
        } else {
            setTimeout(checkPythonAPI, 100);
        }
    }

    checkPythonAPI();

    function initApp() {
        console.log("Dashboard API connected, starting status loop...");
        
        // Listen for message from sub-iframes to navigate back to dashboard if clicked
        window.addEventListener('message', (event) => {
            if (event.data === 'go-to-dashboard') {
                switchTab('dashboard');
            }
        });

        // Set up global handler so iframes can easily tell parent to change tabs
        window.hubSwitchTab = switchTab;

        // Sidebar minimize toggle logic
        const sidebar = document.querySelector('.sidebar');
        const btnSidebarToggle = document.getElementById('btn-sidebar-toggle');
        
        // Restore minimized state on startup
        const isMinimized = localStorage.getItem('sidebar-minimized') === 'true';
        if (isMinimized) {
            sidebar.classList.add('minimized');
        }
        
        if (btnSidebarToggle) {
            btnSidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('minimized');
                const currentlyMinimized = sidebar.classList.contains('minimized');
                localStorage.setItem('sidebar-minimized', currentlyMinimized);
            });
        }

        startStatusPolling();
    }

    function startStatusPolling() {
        updateHubStatus();
        statusInterval = setInterval(updateHubStatus, 1500);
    }

    function updateHubStatus() {
        if (!window.pywebview || !window.pywebview.api) return;

        const startTime = Date.now();
        window.pywebview.api.get_hub_status().then(data => {
            const duration = Date.now() - startTime;
            pingIndicator.textContent = `${duration} ms`;

            if (!data) return;

            let activeBots = [];

            // 1. Process AQW Bot Status
            if (data.aqw && data.aqw.running) {
                activeBots.push("AQW Bot");
                setBotActiveState('aqw', true);
                
                document.getElementById('aqw-user').textContent = data.aqw.username || 'Unknown';
                document.getElementById('aqw-map').textContent = data.aqw.cell ? `${data.aqw.map || '-'} (${data.aqw.cell})` : (data.aqw.map || 'Unknown');
                
                if (data.aqw.hp !== undefined && data.aqw.max_hp !== undefined) {
                    document.getElementById('aqw-stats').textContent = `${data.aqw.hp}/${data.aqw.max_hp} HP | ${data.aqw.mp}/${data.aqw.max_mp} MP`;
                } else {
                    document.getElementById('aqw-stats').textContent = 'Connected';
                }
                
                document.getElementById('aqw-gold').textContent = data.aqw.gold_farmed !== undefined ? data.aqw.gold_farmed.toLocaleString() : '0';
            } else {
                setBotActiveState('aqw', false);
            }

            // 2. Process Slavery Bot Status
            if (data.slavery && data.slavery.running) {
                activeBots.push("Slavery Bot");
                setBotActiveState('slavery', true);
                
                document.getElementById('slavery-count').textContent = `${data.slavery.count} active`;
                renderChips('slavery-accounts', data.slavery.slaves);
            } else {
                setBotActiveState('slavery', false);
            }

            // 3. Process Temple Bot Status
            if (data.temple && data.temple.running) {
                activeBots.push("Temple Bot");
                setBotActiveState('temple', true);
                
                document.getElementById('temple-count').textContent = `${data.temple.count} / 4 active`;
                renderChips('temple-members', data.temple.members);
                
                const templeTimeEl = document.getElementById('temple-time-running');
                if (templeTimeEl) {
                    templeTimeEl.textContent = formatTimeRunning(data.temple.time_running);
                }
            } else {
                setBotActiveState('temple', false);
            }

            // 4. Process Eclipse Bot Status
            if (data.eclipse && data.eclipse.running) {
                activeBots.push("Maid Eclipse");
                setBotActiveState('eclipse', true);
                
                document.getElementById('eclipse-count').textContent = `${data.eclipse.count} / 4 active`;
                renderChips('eclipse-members', data.eclipse.members);
                
                const eclipseTimeEl = document.getElementById('eclipse-time-running');
                if (eclipseTimeEl) {
                    eclipseTimeEl.textContent = formatTimeRunning(data.eclipse.time_running);
                }
            } else {
                setBotActiveState('eclipse', false);
            }

            // 5. Update System Stats
            if (data.system_stats) {
                sysCpu.textContent = `${data.system_stats.cpu}%`;
                sysMem.textContent = `${data.system_stats.memory} MB`;
            }

            // Update Summary Banner
            if (activeBots.length > 0) {
                bannerDot.classList.add('active');
                bannerDescription.textContent = `Running: ${activeBots.join(', ')}`;
            } else {
                bannerDot.classList.remove('active');
                bannerDescription.textContent = 'All bots are currently inactive.';
            }
        }).catch(err => {
            console.error("Failed to fetch hub status:", err);
            pingIndicator.textContent = `Error`;
        });
    }

    function setBotActiveState(botId, isActive) {
        const badge = badges[botId];
        const cardDetails = details[botId];
        const card = cards[botId];

        if (isActive) {
            badge.classList.add('active');
            badge.textContent = 'Active';
            cardDetails.classList.remove('hidden');
            card.classList.add('active-card');
        } else {
            badge.classList.remove('active');
            badge.textContent = 'Offline';
            cardDetails.classList.add('hidden');
            card.classList.remove('active-card');
        }
    }

    function renderChips(containerId, list) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        if (!list || list.length === 0) {
            container.innerHTML = '<span class="chip-empty">None</span>';
            return;
        }

        list.forEach(item => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = item;
            container.appendChild(chip);
        });
    }

    // --- Theme Management ---
    function applyTheme(themeName) {
        document.body.classList.remove("theme-red", "theme-pink", "theme-blue", "theme-green");
        if (themeName !== "default") {
            document.body.classList.add(`theme-${themeName}`);
        }
        currentTheme = themeName;
        localStorage.setItem("global-theme", themeName);
        updateActiveThemeDot(themeName);
        applyThemeToIframes(themeName);
        
        if (window.pywebview && window.pywebview.api && window.pywebview.api.save_theme) {
            window.pywebview.api.save_theme(themeName);
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

    function applyThemeToIframe(iframe, theme) {
        try {
            if (iframe.contentDocument && iframe.contentDocument.body) {
                iframe.contentDocument.body.classList.remove("theme-red", "theme-pink", "theme-blue", "theme-green");
                if (theme !== "default") {
                    iframe.contentDocument.body.classList.add(`theme-${theme}`);
                }

                // Hide redundant brand header inside Hub
                const brand = iframe.contentDocument.querySelector(".brand");
                if (brand) {
                    brand.style.display = "none";
                }
            }
        } catch (e) {
            console.error("Error applying theme/hiding brand to iframe:", e);
        }
    }

    window.applyThemeToIframe = applyThemeToIframe; // Expose globally for lazy loading onload

    function applyThemeToIframes(theme) {
        document.querySelectorAll('.bot-iframe').forEach(iframe => {
            applyThemeToIframe(iframe, theme);
        });
    }

    function initTheme() {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_theme) {
            window.pywebview.api.get_theme().then(theme => {
                applyTheme(theme);
            });
        } else {
            let localTheme = localStorage.getItem("global-theme") || "default";
            applyTheme(localTheme);
        }
    }

    // Set active theme on load & listen for api injection
    initTheme();
    window.addEventListener('pywebviewready', initTheme);

    // Add click listeners to theme dots
    document.querySelectorAll(".theme-dot").forEach(dot => {
        dot.addEventListener("click", () => {
            const selectedTheme = dot.getAttribute("data-theme");
            applyTheme(selectedTheme);
        });
    });

    // --- Global Log Forwarding to nested iframes ---
    window.addSlaveLog = function(username, htmlMsg) {
        document.querySelectorAll('.bot-iframe').forEach(iframe => {
            try {
                if (iframe.contentWindow && iframe.contentWindow.addSlaveLog) {
                    iframe.contentWindow.addSlaveLog(username, htmlMsg);
                }
            } catch (e) {
                console.error("Error forwarding addSlaveLog:", e);
            }
        });
    };

    window.addLog = function(htmlMsg) {
        const iframe = document.getElementById("iframe-aqw");
        try {
            if (iframe && iframe.contentWindow && iframe.contentWindow.addLog) {
                iframe.contentWindow.addLog(htmlMsg);
            }
        } catch (e) {
            console.error("Error forwarding addLog:", e);
        }
    };
});
