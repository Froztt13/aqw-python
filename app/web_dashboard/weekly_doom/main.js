(function () {
    var players = [];

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

    function serverValue() { return document.getElementById('server').value || 'Swordhaven (EU)'; }
    function roomValue() { return parseInt(document.getElementById('room').value || '9099', 10); }

    function renderPlayers(list) {
        players = list || [];
        // manual dropdown
        var sel = document.getElementById('manual-player');
        sel.innerHTML = '<option value="">— manual —</option>';
        // checkbox list
        var box = document.getElementById('player-checks');
        box.innerHTML = '';
        players.forEach(function (p, i) {
            var opt = document.createElement('option');
            opt.value = String(i); opt.textContent = p.user || ('player ' + (i + 1));
            sel.appendChild(opt);

            var label = document.createElement('label');
            label.className = 'chk-label';
            label.style.cssText = 'display:flex;align-items:center;gap:8px;cursor:pointer;padding:7px 10px;border-radius:8px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06)';
            label.innerHTML = '<input type="checkbox" value="' + i + '" style="accent-color:var(--primary-color,#a855f7);cursor:pointer">' +
                '<span style="font-size:.8rem;color:#e2e8f0">' + esc(p.user || '') + '</span>';
            box.appendChild(label);
        });
        document.getElementById('checks-empty').style.display = players.length ? 'none' : 'block';

        sel.onchange = function () {
            var p = players[parseInt(sel.value, 10)];
            if (!p) return;
            document.getElementById('manual-user').value = p.user || '';
            document.getElementById('manual-pass').value = p.pass || '';
        };
    }

    function start(accounts) {
        msg('');
        api().start_bots({ server: serverValue(), room_number: roomValue(), accounts: accounts })
            .then(function (res) {
                if (!res || !res.success) { msg((res && res.error) || 'Failed to start', false); return; }
                var extra = (res.errors && res.errors.length) ? (' (' + res.errors.join('; ') + ')') : '';
                msg('Started ' + (res.started || 0) + ' account(s).' + extra, true);
            });
    }

    function renderStatuses(statuses) {
        var box = document.getElementById('status-list');
        if (!statuses || !statuses.length) { box.innerHTML = '<span class="pill">idle</span>'; return; }
        box.innerHTML = statuses.map(function (s) {
            if (!s.running) return '<span class="pill">' + esc(s.username) + ': done</span>';
            var hp = s.max_hp ? Math.round(s.hp / s.max_hp * 100) : 0;
            return '<span class="pill">' + esc(s.username) + '</span>' +
                '<span class="pill">' + esc(s.map || '-') + ' / ' + esc(s.cell || '-') + '</span>' +
                '<span class="pill">HP ' + hp + '%</span>' +
                (s.is_dead ? '<span class="pill" style="color:#f87171">dead</span>' : '');
        }).join(' ');
    }

    window.addSlaveLog = function (user, html) {
        var log = document.getElementById('log');
        if (!log) return;
        var line = document.createElement('div');
        line.innerHTML = '<span class="who">' + esc(user || '') + '</span> ' + html;
        log.appendChild(line);
        while (log.childNodes.length > 500) { log.removeChild(log.firstChild); }
        log.scrollTop = log.scrollHeight;
    };

    function refreshPlayers() { return window.loadPlayers().then(renderPlayers); }

    window.whenApiReady(function (a) {
        a.load_config().then(function (config) {
            if (config && config.server) { document.getElementById('server').value = config.server; }
            if (config && config.room_number) { document.getElementById('room').value = config.room_number; }
        });
        refreshPlayers();

        document.getElementById('btn-refresh').onclick = function () { refreshPlayers(); };

        document.getElementById('btn-start-manual').onclick = function () {
            var u = document.getElementById('manual-user').value.trim();
            var p = document.getElementById('manual-pass').value;
            if (!u || !p) { msg('Fill username and password.', false); return; }
            start([{ username: u, password: p }]);
        };

        document.getElementById('btn-start-selected').onclick = function () {
            var accounts = [];
            document.querySelectorAll('#player-checks input[type=checkbox]:checked').forEach(function (cb) {
                var p = players[parseInt(cb.value, 10)];
                if (p && p.user) { accounts.push({ username: p.user, password: p.pass || '' }); }
            });
            if (!accounts.length) { msg('Tick at least one player.', false); return; }
            start(accounts);
        };

        document.getElementById('btn-stop').onclick = function () {
            a.stop_bots().then(function () { msg('Stopped.', true); });
        };
        var clearBtn = document.getElementById('btn-clear-logs');
        if (clearBtn) { clearBtn.onclick = function () { document.getElementById('log').innerHTML = ''; }; }

        setInterval(function () { a.get_statuses().then(renderStatuses); }, 1500);
    });
})();
