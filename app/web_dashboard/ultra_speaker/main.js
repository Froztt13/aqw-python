(function () {
    var SLOT_IDS = ['slot1', 'slot2', 'slot3', 'slot4'];
    var roles = [];              // [{role, cls, weapon, helm, cape, scroll}, ...]
    var roleByName = {};

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

    function part(label, val) {
        return '<span class="k">' + label + ':</span> ' + esc(val || '-');
    }

    function roleInfoHtml(role) {
        var info = roleByName[role];
        if (!info) return '<span class="k">No loadout configured for this role.</span>';
        return '<div><span class="cls">' + esc(info.cls || role) + '</span></div>' +
            '<div>' + part('Weapon', info.weapon) + ' &middot; ' + part('Helm', info.helm) + '</div>' +
            '<div>' + part('Cape', info.cape) + ' &middot; ' +
            '<span class="k">Scroll (required):</span> ' + esc(info.scroll || 'Scroll of Enrage') + '</div>' +
            '<span class="hint">Auto-equip: each item is searched in the inventory &amp; bank and equipped automatically.</span>';
    }

    function updateRoleInfo(card) {
        var sel = card.querySelector('.slot-role');
        card.querySelector('[data-roleinfo]').innerHTML = roleInfoHtml(sel.value);
    }

    function buildSlot(i, sId) {
        var card = document.createElement('div');
        card.className = 'slot-card ' + (i % 2 === 0 ? 'sun-theme' : 'moon-theme');
        card.dataset.slot = sId;
        var opts = roles.map(function (r) {
            return '<option value="' + esc(r.role) + '">' + esc(r.role) + '</option>';
        }).join('');
        card.innerHTML =
            '<div class="slot-header" style="display:flex;justify-content:space-between;align-items:center">' +
            '  <div class="slot-title-group" style="display:flex;align-items:center;gap:10px">' +
            '    <div class="slot-icon-box" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:8px;background:rgba(168,85,247,.15);border:1px solid rgba(168,85,247,.3)">' +
            '      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:#c084fc"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>' +
            '    </div>' +
            '    <div style="display:flex;flex-direction:column">' +
            '      <span style="font-size:.88rem;font-weight:700;line-height:1.2">Pane ' + (i + 1) + '</span>' +
            '      <span style="font-size:.68rem;color:var(--text-secondary,#94a3b8);font-weight:500">' + (i === 0 ? 'Leader' : 'Follower') + '</span>' +
            '    </div>' +
            '  </div>' +
            '  <div class="status-badge" data-badge>Offline</div>' +
            '</div>' +
            '<div class="slot-body">' +
            '  <div class="slot-inputs-container" style="display:flex;flex-direction:column;gap:10px">' +
            '    <div class="form-group"><label>Player</label><select class="slot-player"></select></div>' +
            '    <div class="form-group"><label>Role</label><select class="slot-role">' + opts + '</select></div>' +
            '    <div class="form-group"><label>Username</label><input type="text" class="slot-user" placeholder="Username" autocomplete="off"></div>' +
            '    <div class="form-group"><label>Password</label><div class="password-wrapper"><input type="password" class="slot-pass" placeholder="Password" autocomplete="off"></div></div>' +
            '    <div class="role-info" data-roleinfo></div>' +
            '    <div class="slot-status" data-status><span class="pill">idle</span></div>' +
            '  </div>' +
            '</div>';
        attachPlayersDropdown(card.querySelector('.slot-player'), function (user, pass) {
            card.querySelector('.slot-user').value = user;
            card.querySelector('.slot-pass').value = pass;
        });
        card.querySelector('.slot-role').onchange = function () { updateRoleInfo(card); };
        updateRoleInfo(card);
        return card;
    }

    function applyConfig(config) {
        document.getElementById('server').value = config.server || 'Alteon';
        document.getElementById('room').value = config.room_number || 9099;
        document.getElementById('missing-policy').value = config.missing_policy || 'stop';
        var slots = config.slots || {};
        SLOT_IDS.forEach(function (sId, idx) {
            var card = document.querySelector('.slot-card[data-slot="' + sId + '"]');
            var s = slots[sId] || {};
            if (s.username) card.querySelector('.slot-user').value = s.username;
            if (s.password) card.querySelector('.slot-pass').value = s.password;
            card.querySelector('.slot-role').value = s.role || (roles[idx] && roles[idx].role) || '';
            updateRoleInfo(card);
        });
    }

    function collect() {
        var config = {
            server: document.getElementById('server').value || 'Alteon',
            room_number: parseInt(document.getElementById('room').value || '9099', 10),
            missing_policy: document.getElementById('missing-policy').value || 'stop',
            slots: {}
        };
        SLOT_IDS.forEach(function (sId) {
            var card = document.querySelector('.slot-card[data-slot="' + sId + '"]');
            config.slots[sId] = {
                username: card.querySelector('.slot-user').value.trim(),
                password: card.querySelector('.slot-pass').value,
                role: card.querySelector('.slot-role').value
            };
        });
        return config;
    }

    function renderStatus(status) {
        var slots = (status && status.slots) || {};
        SLOT_IDS.forEach(function (sId) {
            var card = document.querySelector('.slot-card[data-slot="' + sId + '"]');
            var badge = card.querySelector('[data-badge]');
            var el = card.querySelector('[data-status]');
            var s = slots[sId];
            if (!s || !s.running) {
                badge.textContent = 'Offline'; badge.style.color = '';
                el.innerHTML = '<span class="pill">idle</span>'; return;
            }
            badge.textContent = 'Online'; badge.style.color = '#34d399';
            var hp = s.max_hp ? Math.round(s.hp / s.max_hp * 100) : 0;
            el.innerHTML =
                '<span class="pill">' + esc(s.username || '-') + '</span>' +
                '<span class="pill">HP ' + hp + '%</span>' +
                '<span class="pill">MP ' + (s.mp || 0) + '</span>' +
                '<span class="pill">' + esc(s.map || '-') + ' / ' + esc(s.cell || '-') + '</span>' +
                (s.is_dead ? '<span class="pill" style="color:#f87171">dead</span>' : '');
        });
    }

    window.addUltraLog = function (kind, key, user, html) {
        var log = document.getElementById('log');
        if (!log) return;
        var line = document.createElement('div');
        line.innerHTML = '<span class="who">' + esc(user || '') + '</span> ' + html;
        log.appendChild(line);
        while (log.childNodes.length > 500) { log.removeChild(log.firstChild); }
        var c = document.getElementById('chk-auto-scroll');
        if (!c || c.checked) { log.scrollTop = log.scrollHeight; }
    };
    window.addSlaveLog = function (user, html) { window.addUltraLog('', '', user, html); };

    window.whenApiReady(function (a) {
        var container = document.getElementById('slots');
        a.get_roles().then(function (r) {
            roles = r || [];
            roleByName = {};
            roles.forEach(function (info) { roleByName[info.role] = info; });
            SLOT_IDS.forEach(function (sId, i) { container.appendChild(buildSlot(i, sId)); });
            return a.load_config();
        }).then(function (config) { applyConfig(config || {}); });

        document.getElementById('btn-start').onclick = function () {
            msg('');
            a.start_party(collect()).then(function (res) {
                if (!res || !res.success) { msg((res && res.error) || 'Failed to start', false); return; }
                msg('Party starting...', true);
            });
        };
        document.getElementById('btn-stop').onclick = function () {
            a.stop_party().then(function () { msg('Stopped.', true); });
        };
        var clearBtn = document.getElementById('btn-clear-logs');
        if (clearBtn) { clearBtn.onclick = function () { document.getElementById('log').innerHTML = ''; }; }

        setInterval(function () { a.get_status().then(renderStatus); }, 1500);
    });
})();
