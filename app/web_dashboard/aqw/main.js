(function () {
    var BOT_PRESET = [
        "Gem of Nulgath", "Diamond of Nulgath", "Voucher of Nulgath (non-mem)",
        "Tainted Gem", "Dark Crystal Shard"
    ];

    //: One entry per tab.  The editor is a single persistent form that reads
    //: from / writes to accounts[active], so switching tabs never rebuilds it.
    var accounts = [];
    var active = 0;
    var runningNames = {};   // username -> true while its bot is running

    function api() { return window.pywebview && window.pywebview.api; }

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
        });
    }

    function msg(text, ok) {
        var el = document.getElementById('msg');
        if (!el) return;
        el.textContent = text || '';
        el.className = 'cfg-msg' + (text ? (ok ? ' ok' : ' err') : '');
    }

    function el(id) { return document.getElementById(id); }

    function accountTemplate() {
        return {
            username: "", password: "", server: "Artix", room_number: "1",
            bot_path: "", farm_class: "", solo_class: "",
            whitelist: BOT_PRESET.slice(),
            auto_relogin: true, show_chat: true, mute_spam: true, anti_mod: true,
            bot_external: false, bot_parent_dir: ""
        };
    }

    function current() { return accounts[active]; }

    // ---- tabs -------------------------------------------------------
    function tabLabel(i) {
        var a = accounts[i] || {};
        var user = (a.username || '').trim();
        // Running -> the account name; otherwise a default name.
        if (user && runningNames[user]) return user;
        return 'Account ' + (i + 1);
    }

    function renderTabs() {
        var bar = el('account-tabs');
        bar.innerHTML = '';
        accounts.forEach(function (a, i) {
            var wrap = document.createElement('div');
            wrap.className = 'aqw-tab' + (i === active ? ' active' : '');

            var lbl = document.createElement('button');
            lbl.className = 'aqw-tab-label';
            lbl.innerHTML = ((tabLabel(i) !== ('Account ' + (i + 1))) ? '&#9679; ' : '') + esc(tabLabel(i));
            lbl.title = tabLabel(i);
            lbl.onclick = function () { active = i; renderTabs(); loadEditor(); };

            var x = document.createElement('button');
            x.className = 'aqw-tab-x';
            x.textContent = '\u00d7';
            x.disabled = !!runningNames[(a.username || '').trim()];
            x.title = x.disabled ? 'Stop the bot before removing' : 'Remove account';
            x.onclick = function (e) { e.stopPropagation(); if (x.disabled) return; removeAccount(i); };

            wrap.appendChild(lbl);
            wrap.appendChild(x);
            bar.appendChild(wrap);
        });
    }

    // ---- editor <-> accounts ---------------------------------------
    function loadEditor() {
        var a = current() || accountTemplate();
        el('f-user').value = a.username || '';
        el('f-pass').value = a.password || '';
        el('f-server').value = a.server || 'Artix';
        el('f-room').value = a.room_number || '1';
        el('f-script').value = a.bot_path || '';
        el('f-script').dataset.external = a.bot_external ? '1' : '';
        el('f-script').dataset.parent = a.bot_parent_dir || '';
        el('f-farm').value = a.farm_class || '';
        el('f-solo').value = a.solo_class || '';
        el('f-whitelist').value = Array.isArray(a.whitelist) ? a.whitelist.join(', ') : (a.whitelist || '');
        el('f-player').value = '';
        el('editor-title').textContent = tabLabel(active);
        renderEditorStatus();
        renderLog();
        el('chk-items').checked = !!a._showItems;
        updateItemsCard();
    }

    function syncFromEditor() {
        var a = current();
        if (!a) return;
        a.username = el('f-user').value;
        a.password = el('f-pass').value;
        a.server = el('f-server').value || 'Artix';
        a.room_number = el('f-room').value || '1';
        a.bot_path = el('f-script').value;
        a.bot_external = el('f-script').dataset.external === '1';
        a.bot_parent_dir = el('f-script').dataset.parent || '';
        a.farm_class = el('f-farm').value;
        a.solo_class = el('f-solo').value;
        a.whitelist = el('f-whitelist').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    }

    // ---- items explorer (inventory / bank / temp) -------------------
    var itemsTab = 'inventory';
    var itemsData = { inventory: [], bank: [], temp: [] };
    var itemsSig = '';

    function itemsKey() {
        var a = current();
        return a && (a.username || '').trim();
    }

    function updateItemsCard() {
        var a = current() || {};
        var card = el('items-card');
        if (!card) return;
        var show = !!a._showItems;
        card.style.display = show ? '' : 'none';
        if (show) {
            el('items-owner').textContent = itemsKey() || '(no username)';
            pollItems();
        }
    }

    function pollItems() {
        var card = el('items-card');
        if (!card || card.style.display === 'none') return;
        var key = itemsKey();
        if (!key) { itemsData = { inventory: [], bank: [], temp: [] }; renderItems(); return; }
        api().get_items(key).then(function (data) {
            itemsData = data || { inventory: [], bank: [], temp: [] };
            renderItems();
        }).catch(function () {});
    }

    function renderItems() {
        var box = el('items-groups');
        if (!box) return;
        var items = (itemsData && itemsData[itemsTab]) || [];

        // Nothing changed -> don't rebuild (no flicker, no scroll jump).
        var sig = itemsTab + '\u0000' + JSON.stringify(itemsData);
        if (sig === itemsSig && box.childNodes.length) { return; }

        // Keep the reader's place: remember each group body's scroll and the page.
        var page = document.querySelector('.app-body') || document.scrollingElement;
        var pageTop = page ? page.scrollTop : 0;
        var keep = {};
        box.querySelectorAll('.item-group').forEach(function (g) {
            var t = g.querySelector('.item-group-title');
            var b = g.querySelector('.item-group-body');
            if (t && b) { keep[t.dataset.slot || ''] = b.scrollTop; }
        });

        itemsSig = sig;
        if (!items.length) {
            box.innerHTML = '<p class="cfg-empty">No items.</p>';
        } else {
            var groups = {};
            items.forEach(function (it) {
                var slot = it.slot || 'Misc';
                if (!groups[slot]) { groups[slot] = []; }
                groups[slot].push(it);
            });
            box.innerHTML = Object.keys(groups).sort().map(function (slot) {
                var rows = groups[slot].map(function (it) {
                    var meta = [];
                    if (it.level) { meta.push('Lv' + it.level); }
                    if (it.dps) { meta.push('DPS ' + it.dps); }
                    if (it.rarity) { meta.push('R' + it.rarity); }
                    if (it.enh) { meta.push('Enh: ' + it.enh); }
                    if (it.equipped) { meta.push('equipped'); }
                    return '<div class="item-row">' +
                        '<span class="qty">' + (it.qty || 1) + 'x</span>' +
                        '<span class="nm">' + esc(it.name) + '</span>' +
                        (meta.length ? '<span class="meta">' + esc(meta.join(' \u00b7 ')) + '</span>' : '') +
                        '</div>';
                }).join('');
                return '<div class="item-group"><div class="item-group-title" data-slot="' + esc(slot) + '">' + esc(slot) +
                    ' <span class="k">(' + groups[slot].length + ')</span></div>' +
                    '<div class="item-group-body">' + rows + '</div></div>';
            }).join('');
            box.querySelectorAll('.item-group').forEach(function (g) {
                var t = g.querySelector('.item-group-title');
                var b = g.querySelector('.item-group-body');
                if (t && b && keep[t.dataset.slot || ''] != null) {
                    b.scrollTop = keep[t.dataset.slot || ''];
                }
            });
        }
        if (page) { page.scrollTop = pageTop; }
    }

    // ---- accounts ---------------------------------------------------
    function addAccount(acc) {
        accounts.push(acc || accountTemplate());
        active = accounts.length - 1;
        renderTabs();
        loadEditor();
    }

    function removeAccount(i) {
        accounts.splice(i, 1);
        if (!accounts.length) { accounts.push(accountTemplate()); }
        if (active >= accounts.length) { active = accounts.length - 1; }
        renderTabs();
        loadEditor();
    }

    function accountPayload(acc) {
        return {
            username: (acc.username || '').trim(),
            password: acc.password || '',
            server: acc.server || 'Artix',
            room_number: acc.room_number || '1',
            bot_path: (acc.bot_path || '').trim(),
            farm_class: (acc.farm_class || '').trim(),
            solo_class: (acc.solo_class || '').trim(),
            whitelist: acc.whitelist || [],
            auto_relogin: true, show_chat: true, mute_spam: true, anti_mod: true,
            bot_external: !!acc.bot_external,
            bot_parent_dir: acc.bot_parent_dir || ''
        };
    }

    // ---- status -----------------------------------------------------
    function setEditorDisabled(disabled) {
        ['f-player', 'f-user', 'f-pass', 'f-server', 'f-room',
         'f-script', 'f-farm', 'f-solo', 'f-whitelist', 'btn-browse'].forEach(function (id) {
            var node = el(id);
            if (node) { node.disabled = disabled; }
        });
    }

    function renderAccountToggle(running) {
        var btn = el('btn-account-toggle');
        if (!btn) return;
        if (running) { btn.textContent = 'STOP'; btn.className = 'btn btn-danger btn-small'; }
        else { btn.textContent = 'START'; btn.className = 'btn btn-success btn-small'; }
    }

    function renderEditorStatus() {
        var a = current() || {};
        var user = (a.username || '').trim();
        var badge = el('editor-badge');
        var sub = el('editor-sub');
        var st = el('editor-status');
        var s = runningNames[user] ? runningStatus[user] : null;
        renderAccountToggle(!!s);
        setEditorDisabled(!!s);
        if (!s) {
            badge.textContent = 'Offline'; badge.style.color = '';
            sub.textContent = 'not running';
            st.innerHTML = '<span class="pill">idle</span>';
            return;
        }
        badge.textContent = 'Online'; badge.style.color = '#34d399';
        sub.textContent = 'running';
        var hp = s.max_hp ? Math.round(s.hp / s.max_hp * 100) : 0;
        st.innerHTML =
            '<span class="pill">' + esc(s.map || '-') + ' / ' + esc(s.cell || '-') + '</span>' +
            '<span class="pill">HP ' + hp + '%</span>' +
            '<span class="pill">MP ' + (s.mp || 0) + '</span>' +
            (s.is_dead ? '<span class="pill" style="color:#f87171">dead</span>' : '');
    }

    var runningStatus = {};   // username -> status object

    function setStatuses(statuses) {
        runningNames = {};
        runningStatus = {};
        (statuses || []).forEach(function (s) {
            if (s.running) { runningNames[s.key] = true; runningStatus[s.key] = s; }
        });
        renderTabs();
        el('editor-title').textContent = tabLabel(active);
        renderEditorStatus();
    }

    // ---- log (per tab) ---------------------------------------------
    var buffers = {};        // key -> [html line, ...]
    var MAX_LINES = 500;

    function autoScrollOn() {
        var c = el('chk-auto-scroll');
        return !c || c.checked;
    }

    function activeKey() {
        var a = current();
        var u = a && (a.username || '').trim();
        return u || '__system__';
    }

    function renderLog() {
        var log = el('log');
        if (!log) return;
        var lines = buffers[activeKey()] || [];
        log.innerHTML = lines.map(function (h) { return '<div>' + h + '</div>'; }).join('');
        if (autoScrollOn()) { log.scrollTop = log.scrollHeight; }
    }

    function appendLog(key, html) {
        // A line belongs to its account tab; anything else (System/unknown)
        // goes to whichever tab is on screen.
        var isAccount = accounts.some(function (a) { return (a.username || '').trim() === key; });
        var target = isAccount ? key : activeKey();
        var line = '<span class="who">' + esc(key || '') + '</span> ' + html;
        if (!buffers[target]) { buffers[target] = []; }
        buffers[target].push(line);
        while (buffers[target].length > MAX_LINES) { buffers[target].shift(); }
        if (target === activeKey()) {
            var log = el('log');
            if (log) {
                var d = document.createElement('div');
                d.innerHTML = line;
                log.appendChild(d);
                while (log.childNodes.length > MAX_LINES) { log.removeChild(log.firstChild); }
                if (autoScrollOn()) { log.scrollTop = log.scrollHeight; }
            }
        }
    }

    window.addSoloLog = function (key, html) { appendLog(key, html); };
    window.addSlaveLog = function (user, html) { appendLog(user, html); };

    // ---- wire -------------------------------------------------------
    window.whenApiReady(function (a) {
        ['f-user', 'f-pass', 'f-room', 'f-farm', 'f-solo', 'f-whitelist'].forEach(function (id) {
            el(id).addEventListener('input', function () { syncFromEditor(); renderTabs(); });
        });
        el('f-server').addEventListener('change', syncFromEditor);
        el('f-script').addEventListener('change', syncFromEditor);
        el('f-server').addEventListener('input', syncFromEditor);

        attachPlayersDropdown(el('f-player'), function (u, p) {
            el('f-user').value = u;
            el('f-pass').value = p;
            syncFromEditor();
            renderTabs();
        });

        el('btn-browse').onclick = function () {
            a.select_script().then(function (result) {
                if (!result) return;
                el('f-script').value = result.path || '';
                el('f-script').dataset.external = result.external ? '1' : '';
                el('f-script').dataset.parent = result.parent_dir || '';
                syncFromEditor();
            });
        };

        el('btn-add').onclick = function () { addAccount(); };

        el('btn-account-toggle').onclick = function () {
            syncFromEditor();
            var acc = current() || {};
            var user = (acc.username || '').trim();
            if (runningNames[user]) {
                msg('');
                a.stop_one(user).then(function (res) {
                    if (!res || !res.success) { msg((res && res.error) || 'Failed to stop', false); return; }
                    msg('Stopped ' + user + '.', true);
                    a.get_statuses().then(setStatuses);
                });
            } else {
                if (!user) { msg('Username is required.', false); return; }
                msg('');
                a.save_config({ accounts: accounts.map(function (x) { return accountPayload(x); }) });
                a.start_one(accountPayload(acc)).then(function (res) {
                    if (!res || !res.success) { msg((res && res.error) || 'Failed to start', false); return; }
                    msg('Started ' + user + '.', true);
                    a.get_statuses().then(setStatuses);
                });
            }
        };
        el('btn-start').onclick = function () {
            syncFromEditor();
            var payload = accounts.map(function (acc) { return accountPayload(acc); });
            msg('');
            a.start_bots({ accounts: payload }).then(function (res) {
                if (!res || !res.success) { msg((res && res.error) || 'Failed to start', false); return; }
                var extra = (res.errors && res.errors.length) ? (' (' + res.errors.join('; ') + ')') : '';
                msg('Started ' + (res.started || 0) + ' account(s).' + extra, true);
                a.get_statuses().then(setStatuses);
            });
        };
        el('btn-stop').onclick = function () {
            a.stop_bots().then(function () {
                runningNames = {}; runningStatus = {};
                renderTabs(); el('editor-title').textContent = tabLabel(active); renderEditorStatus();
                msg('Stopped.', true);
            });
        };
        var clearBtn = el('btn-clear-logs');
        if (clearBtn) { clearBtn.onclick = function () { buffers[activeKey()] = []; el('log').innerHTML = ''; }; }

        a.load_config().then(function (config) {
            var list = (config && config.accounts) || [];
            accounts = list.length ? list : [accountTemplate()];
            active = 0;
            renderTabs();
            loadEditor();
        });

        setInterval(function () { a.get_statuses().then(setStatuses); }, 1500);

        var itemsChk = el('chk-items');
        if (itemsChk) {
            itemsChk.onchange = function () {
                var a2 = current();
                if (a2) { a2._showItems = itemsChk.checked; }
                updateItemsCard();
            };
        }
        document.querySelectorAll('#items-tabs .items-tab').forEach(function (b) {
            b.onclick = function () {
                itemsTab = b.dataset.list || 'inventory';
                document.querySelectorAll('#items-tabs .items-tab').forEach(function (x) {
                    x.classList.toggle('active', x === b);
                });
                pollItems();
            };
        });
        setInterval(pollItems, 2000);
    });
})();
