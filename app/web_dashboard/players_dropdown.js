// Shared helper: fill a <select> from the Config Player list (players.json).
// Manual entry is always kept -- picking from the dropdown just fills the
// existing username/password inputs, which stay editable.
(function () {
  function api() {
    try { return window.pywebview && window.pywebview.api; } catch (e) { return null; }
  }

  // Resolve once the injected pywebview bridge is available.
  window.whenApiReady = function (fn, tries) {
    tries = tries || 0;
    if (api()) { fn(api()); return; }
    if (tries > 40) { return; }
    setTimeout(function () { window.whenApiReady(fn, tries + 1); }, 250);
  };

  window.loadPlayers = function () {
    var a = api();
    if (!a || !a.list_players) return Promise.resolve([]);
    return a.list_players().catch(function () { return []; });
  };

  // Fill `select` with a "manual" option plus one option per saved player.
  // `onPick(user, pass)` fires when a saved player is chosen.
  window.attachPlayersDropdown = function (select, onPick) {
    if (!select) return;
    window.loadPlayers().then(function (players) {
      var prev = select.value;
      select.innerHTML = '<option value="">— manual —</option>';
      (players || []).forEach(function (p, i) {
        var opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = p.user || ('player ' + (i + 1));
        opt.dataset.user = p.user || '';
        opt.dataset.pass = p.pass || '';
        select.appendChild(opt);
      });
      if (prev) { select.value = prev; }
      select.onchange = function () {
        var opt = select.options[select.selectedIndex];
        if (!opt || opt.value === '') return;
        if (onPick) onPick(opt.dataset.user || '', opt.dataset.pass || '');
      };
    });
  };

  // Best-effort wiring for the existing menus (temple/eclipse/slavery): insert a
  // player dropdown above every "<x>-username" input and fill it + its matching
  // "<x>-password" input. Manual typing still works.
  window.autoWirePlayersDropdowns = function () {
    var inputs = document.querySelectorAll('input[id$="-username"], input#input-username');
    Array.prototype.forEach.call(inputs, function (userEl) {
      if (userEl.dataset && userEl.dataset.playerWired) return;
      var passEl = userEl.id ? document.getElementById(userEl.id.replace(/-username$/, '-password')) : null;
      if (!passEl) return;
      userEl.dataset.playerWired = '1';
      var select = document.createElement('select');
      select.className = 'cfg-player-inline';
      select.style.cssText = 'width:100%;margin-bottom:6px;padding:7px 9px;border-radius:7px;' +
        'border:1px solid rgba(148,163,184,.25);background:rgba(9,10,16,.6);color:var(--text-primary,#F8FAFC);';
      userEl.parentNode.insertBefore(select, userEl);
      window.attachPlayersDropdown(select, function (u, p) {
        userEl.value = u;
        passEl.value = p;
        try {
          userEl.dispatchEvent(new Event('input', { bubbles: true }));
          passEl.dispatchEvent(new Event('input', { bubbles: true }));
        } catch (e) { /* older engines */ }
      });
    });
  };

  window.whenApiReady(function () {
    window.autoWirePlayersDropdowns();
    try {
      new MutationObserver(window.autoWirePlayersDropdowns)
        .observe(document.body, { childList: true, subtree: true });
    } catch (e) { /* no MutationObserver */ }
  });
})();
