(function () {
    var editing = -1;   // index currently being edited

    function api() { return window.pywebview && window.pywebview.api; }

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
        });
    }

    function msg(text, ok) {
        var el = document.getElementById('msg');
        el.textContent = text || '';
        el.className = 'cfg-msg' + (text ? (ok ? ' ok' : ' err') : '');
    }

    function render(players) {
        var rows = document.getElementById('rows');
        rows.innerHTML = '';
        document.getElementById('empty').style.display = (players && players.length) ? 'none' : 'block';

        (players || []).forEach(function (p, i) {
            var tr = document.createElement('tr');
            if (i === editing) {
                tr.innerHTML =
                    '<td>' + (i + 1) + '</td>' +
                    '<td><input class="edit-user" type="text" value="' + esc(p.user) + '"></td>' +
                    '<td><input class="edit-pass" type="password" value="' + esc(p.pass) + '"></td>' +
                    '<td><button class="cfg-btn small save">Save</button>' +
                    '<button class="cfg-btn small ghost cancel">Cancel</button></td>';
                tr.querySelector('.save').onclick = function () {
                    api().update_player(i, tr.querySelector('.edit-user').value,
                                         tr.querySelector('.edit-pass').value).then(function (res) {
                        if (!res || !res.success) { msg((res && res.error) || 'Failed', false); return; }
                        editing = -1; msg('Saved.', true); refresh();
                    });
                };
                tr.querySelector('.cancel').onclick = function () { editing = -1; refresh(); };
            } else {
                tr.innerHTML =
                    '<td>' + (i + 1) + '</td>' +
                    '<td>' + esc(p.user) + '</td>' +
                    '<td class="masked">••••••</td>' +
                    '<td><button class="cfg-btn small edit">Edit</button>' +
                    '<button class="cfg-btn small danger del">Delete</button></td>';
                tr.querySelector('.edit').onclick = function () { editing = i; refresh(); };
                tr.querySelector('.del').onclick = function () {
                    api().delete_player(i).then(function (res) {
                        if (!res || !res.success) { msg((res && res.error) || 'Failed', false); return; }
                        editing = -1; msg('Deleted.', true); refresh();
                    });
                };
            }
            rows.appendChild(tr);
        });
    }

    function refresh() {
        api().list_players().then(function (players) { render(players || []); });
    }

    window.whenApiReady(function () {
        document.getElementById('btn-refresh').onclick = function () {
            editing = -1;
            msg('Reloaded from players.json.', true);
            refresh();
        };
        document.getElementById('btn-add').onclick = function () {
            var u = document.getElementById('new-user').value;
            var p = document.getElementById('new-pass').value;
            api().add_player(u, p).then(function (res) {
                if (!res || !res.success) { msg((res && res.error) || 'Failed', false); return; }
                document.getElementById('new-user').value = '';
                document.getElementById('new-pass').value = '';
                msg('Added.', true); refresh();
            });
        };
        refresh();
    });
})();
