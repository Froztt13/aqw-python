class ServerSelect extends HTMLElement {
    connectedCallback() {
        const id = this.getAttribute('id') || 'select-server';
        const defaultValue = this.getAttribute('value') || 'Artix';
        this.innerHTML = `
            <div class="select-wrapper">
                <select id="${id}">
                    <option value="Artix">Artix</option>
                    <option value="Gravelyn">Gravelyn</option>
                    <option value="Cysero">Cysero</option>
                    <option value="Sir Ver">Sir Ver</option>
                    <option value="Alteon">Alteon</option>
                    <option value="Espada">Espada</option>
                    <option value="Yorumi">Yorumi</option>
                    <option value="Twilly">Twilly</option>
                    <option value="Twig">Twig</option>
                    <option value="Sepulchure">Sepulchure</option>
                    <option value="Safiria">Safiria</option>
                    <option value="Swordhaven (EU)">Swordhaven (EU)</option>
                    <option value="Galanoth">Galanoth</option>
                    <option value="Yokai (SEA)">Yokai (SEA)</option>
                </select>
            </div>
        `;
        const select = this.querySelector('select');
        select.value = defaultValue;
    }
}
customElements.define('server-select', ServerSelect);

class BotControlButtons extends HTMLElement {
    connectedCallback() {
        const startId = this.getAttribute('start-id') || 'btn-start';
        const stopId = this.getAttribute('stop-id') || 'btn-stop';
        const startLabel = this.getAttribute('start-label') || 'Start';
        const stopLabel = this.getAttribute('stop-label') || 'Stop';
        
        this.innerHTML = `
            <button class="btn btn-success" id="${startId}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                <span>${startLabel}</span>
            </button>
            <button class="btn btn-danger hidden" id="${stopId}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
                    <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
                </svg>
                <span>${stopLabel}</span>
            </button>
        `;
    }
}
customElements.define('bot-control-buttons', BotControlButtons);

class SettingsButton extends HTMLElement {
    connectedCallback() {
        const id = this.getAttribute('id') || 'btn-toggle-settings';
        const title = this.getAttribute('title') || 'Settings';
        this.innerHTML = `
            <button class="btn btn-secondary btn-icon-only" id="${id}" title="${title}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px; pointer-events: none;">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
            </button>
        `;
    }
}
customElements.define('settings-button', SettingsButton);

class DurationCounter extends HTMLElement {
    connectedCallback() {
        const id = this.getAttribute('id') || 'duration-counter';
        const valId = this.getAttribute('val-id') || 'duration-val';
        this.innerHTML = `
            <div class="duration-counter hidden" id="${id}" style="color: var(--primary-color); font-family: 'Fira Code', monospace; font-size: 0.85rem; font-weight: 600; padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.2); background-color: rgba(245, 158, 11, 0.05); display: flex; align-items: center; gap: 6px; height: 38px;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span id="${valId}">00:00:00</span>
            </div>
        `;
    }
}
customElements.define('duration-counter', DurationCounter);
