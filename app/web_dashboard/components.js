class ServerSelect extends HTMLElement {
    get value() {
        const select = this.querySelector('select');
        return select ? select.value : (this.getAttribute('value') || 'Artix');
    }
    set value(val) {
        this.setAttribute('value', val);
        const select = this.querySelector('select');
        if (select) {
            select.value = val;
        }
    }
    get disabled() {
        const select = this.querySelector('select');
        return select ? select.disabled : false;
    }
    set disabled(val) {
        const select = this.querySelector('select');
        if (select) {
            select.disabled = val;
        }
    }
    connectedCallback() {
        const id = this.getAttribute('id') || 'select-server';
        const defaultValue = this.getAttribute('value') || 'Artix';
        this.innerHTML = `
            <div class="select-wrapper">
                <select id="${id}-inner">
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
        if (select) {
            select.value = defaultValue;
            select.addEventListener('change', () => {
                this.setAttribute('value', select.value);
            });
        }
    }
}
customElements.define('server-select', ServerSelect);

class BotControlButtons extends HTMLElement {
    connectedCallback() {
        const startId = this.getAttribute('start-id') || 'btn-start';
        const stopId = this.getAttribute('stop-id') || 'btn-stop';
        const startLabel = this.getAttribute('start-label') || 'START';
        const stopLabel = this.getAttribute('stop-label') || 'STOP';

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
        const label = this.getAttribute('label');
        const btnClass = label ? 'btn btn-secondary btn-icon-with-text' : 'btn btn-secondary btn-icon-only';
        const labelHtml = label ? `<span>${label}</span>` : '';
        this.innerHTML = `
            <button type="button" class="${btnClass}" id="${id}" title="${title}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon" style="width: 16px; height: 16px; pointer-events: none;">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1 2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                ${labelHtml}
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

class ClearedCounter extends HTMLElement {
    connectedCallback() {
        const id = this.getAttribute('id') || 'cleared-counter';
        const valId = this.getAttribute('val-id') || 'cleared-val';
        this.innerHTML = `
            <div class="cleared-counter hidden" id="${id}" style="color: #10b981; font-family: 'Fira Code', monospace; font-size: 0.85rem; font-weight: 600; padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.25); background-color: rgba(16, 185, 129, 0.08); display: flex; align-items: center; gap: 6px; height: 38px;" title="Cleared Count">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Cleared: <strong id="${valId}">0</strong></span>
            </div>
        `;
    }
}
customElements.define('cleared-counter', ClearedCounter);

class ItemSlotCard extends HTMLElement {
    connectedCallback() {
        const slotId = this.getAttribute('slot-id') || 'slot1';
        const feature = (this.getAttribute('feature') || 'temple').toLowerCase();
        const theme = this.getAttribute('theme') || 'sun-theme';
        const roleTitle = this.getAttribute('title') || 'Master';
        const roleType = this.getAttribute('role-type') || (theme.includes('sun') ? 'sun' : 'moon');
        const classPlaceholder = this.getAttribute('class-placeholder') || 'ArchPaladin';
        const isSun = theme.includes('sun') || roleType === 'sun';

        let checkboxOptionsHtml = '';
        if (feature === 'temple') {
            checkboxOptionsHtml = `
                <div class="checkbox-options" style="display: flex; align-items: center; margin-top: 4px;">
                    <label class="chk-label" style="display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 7px 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); width: 100%;">
                        <input type="checkbox" id="${slotId}-is-taunter" style="accent-color: var(--primary-color, #a855f7); cursor: pointer;">
                        <span style="font-size: 0.78rem; font-weight: 500; color: #e2e8f0;">Taunter</span>
                    </label>
                </div>
            `;
        } else {
            checkboxOptionsHtml = `
                <div class="checkbox-options" style="display: flex; flex-direction: column; gap: 6px; position: relative; margin-top: 4px;">
                    <label class="chk-label" style="display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 7px 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06);">
                        <input type="checkbox" class="slot-light-gather" id="${slotId}-light-gather" checked style="accent-color: var(--primary-color, #a855f7); cursor: pointer;">
                        <span style="font-size: 0.78rem; font-weight: 500; color: #e2e8f0;">Light Gather Taunter</span>
                    </label>
                    ${slotId === 'slot3' ? `
                    <label class="chk-label" style="display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 7px 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06);">
                        <input type="checkbox" class="slot-moon-haze" id="slot3-moon-haze" checked style="accent-color: var(--primary-color, #a855f7); cursor: pointer;">
                        <span style="font-size: 0.78rem; font-weight: 500; color: #e2e8f0;">Moon Haze Taunter</span>
                    </label>` : ''}
                    ${slotId === 'slot4' ? `
                    <label class="chk-label" style="display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 7px 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06);">
                        <input type="checkbox" class="slot-sunset-knight" id="slot4-sunset-knight" checked style="accent-color: var(--primary-color, #a855f7); cursor: pointer;">
                        <span style="font-size: 0.78rem; font-weight: 500; color: #e2e8f0;">Sunset Knight Taunter</span>
                    </label>` : ''}
                </div>
            `;
        }

        const roleIcon = isSun
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px; color: #f59e0b;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px; color: #c084fc;"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

        let roleSubtitle = '';
        if (feature === 'eclipse') {
            if (slotId === 'slot1') roleSubtitle = 'Master / Odd';
            else if (slotId === 'slot2') roleSubtitle = 'Slave / Even';
            else if (slotId === 'slot3') roleSubtitle = 'Slave / Odd';
            else if (slotId === 'slot4') roleSubtitle = 'Slave / Even';
        } else {
            if (slotId === 'slot1') roleSubtitle = 'Leader';
            else roleSubtitle = 'Follower';
        }

        const headerHtml = `
            <div class="slot-title-group" style="display: flex; align-items: center; gap: 10px;">
                <div class="slot-icon-box ${isSun ? 'sun' : 'moon'}" style="display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 8px; background: ${isSun ? 'rgba(245, 158, 11, 0.15)' : 'rgba(168, 85, 247, 0.15)'}; border: 1px solid ${isSun ? 'rgba(245, 158, 11, 0.3)' : 'rgba(168, 85, 247, 0.3)'};">
                    ${roleIcon}
                </div>
                <div style="display: flex; flex-direction: column;">
                    <span class="badge-role ${isSun ? 'sun' : 'moon'}" style="font-size: 0.88rem; font-weight: 700; line-height: 1.2;">${roleTitle}</span>
                    <span style="font-size: 0.68rem; color: var(--text-secondary, #94a3b8); font-weight: 500;">${roleSubtitle}</span>
                </div>
            </div>
            <div class="status-badge" id="badge-${slotId}">Offline</div>
        `;

        const runningExtraHtml = feature === 'temple'
            ? `<div class="info-row"><span class="info-label">Taunter</span><span class="info-value" id="${slotId}-info-taunter">-</span></div>`
            : '';

        this.innerHTML = `
            <div class="slot-card ${theme}" id="card-${slotId}">
                <div class="slot-header">
                    ${headerHtml}
                </div>
                <div class="slot-body">
                    <!-- Inputs -->
                    <div class="slot-inputs-container" id="${slotId}-inputs-container" style="display: flex; flex-direction: column; gap: 10px;">
                        <div class="form-group">
                            <label>Username</label>
                            <input type="text" id="${slotId}-username" class="slot-username" placeholder="Username">
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <div class="password-wrapper">
                                <input type="password" id="${slotId}-password" class="slot-password" placeholder="Password">
                                <button type="button" class="btn-toggle-password" tabindex="-1" title="Toggle password visibility">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px; pointer-events: none;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                                </button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Class</label>
                            <input type="text" id="${slotId}-class" class="slot-class" placeholder="${classPlaceholder}">
                        </div>
                        ${checkboxOptionsHtml}
                    </div>

                    <!-- Running Info Display -->
                    <div class="slot-running-display hidden" id="${slotId}-running-display">
                        <div class="info-row">
                            <span class="info-label">Active Account</span>
                            <span class="info-value" id="${slotId}-info-username">-</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Class</span>
                            <span class="info-value" id="${slotId}-info-class">-</span>
                        </div>
                        ${runningExtraHtml}
                        <div class="info-row">
                            <span class="info-label">Scroll of Enrage</span>
                            <span class="info-value" id="${slotId}-info-soe" style="font-weight: bold;">0 SoE</span>
                        </div>
                    </div>
                    
                    <!-- Telemetry Display (Hidden by default) -->
                    <div class="telemetry-panel hidden" id="telemetry-${slotId}">
                        <div class="telemetry-row">
                            <span class="tel-label">Map</span>
                            <span class="tel-val" id="tel-${slotId}-map">-</span>
                        </div>
                        <div class="telemetry-row">
                            <span class="tel-label">Cell</span>
                            <span class="tel-val" id="tel-${slotId}-cell">-</span>
                        </div>
                        <div class="vitals-group">
                            <div class="vital-bar-container">
                                <div class="vital-label">HP: <span id="val-${slotId}-hp">0/0</span></div>
                                <div class="vital-bar hp"><div class="fill" id="bar-${slotId}-hp" style="width: 0%"></div></div>
                            </div>
                            <div class="vital-bar-container">
                                <div class="vital-label">MP: <span id="val-${slotId}-mp">0/0</span></div>
                                <div class="vital-bar mp"><div class="fill" id="bar-${slotId}-mp" style="width: 0%"></div></div>
                            </div>
                        </div>
                        <div class="telemetry-row flex-col" style="margin-top: 8px;">
                            <div id="cooldowns-${slotId}" class="cooldowns-container cooldowns-grid">
                                <div class="skill-cd-badge ready" id="cd-${slotId}-0"><span class="skill-idx">AA</span><span class="skill-cd-val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg></span></div>
                                <div class="skill-cd-badge ready" id="cd-${slotId}-1"><span class="skill-idx">1</span><span class="skill-cd-val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg></span></div>
                                <div class="skill-cd-badge ready" id="cd-${slotId}-2"><span class="skill-idx">2</span><span class="skill-cd-val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg></span></div>
                                <div class="skill-cd-badge ready" id="cd-${slotId}-3"><span class="skill-idx">3</span><span class="skill-cd-val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg></span></div>
                                <div class="skill-cd-badge ready" id="cd-${slotId}-4"><span class="skill-idx">4</span><span class="skill-cd-val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg></span></div>
                                <div class="skill-cd-badge skill-5-badge ready" id="cd-${slotId}-5"><span class="skill-idx">5</span><span class="skill-cd-val"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="width: 8px; height: 8px; display: block; margin: 0 auto;"><polyline points="20 6 9 17 4 12"></polyline></svg></span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const btn = this.querySelector('.btn-toggle-password');
        if (btn && !btn.dataset.bound) {
            btn.dataset.bound = 'true';
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                const input = btn.previousElementSibling;
                if (!input) return;
                const isPassword = input.type === 'password';
                input.type = isPassword ? 'text' : 'password';
                btn.innerHTML = isPassword
                    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px; pointer-events: none;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
                    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px; pointer-events: none;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
            });
        }
    }
}
customElements.define('item-slot-card', ItemSlotCard);
customElements.define('slot-card', class extends ItemSlotCard { });

