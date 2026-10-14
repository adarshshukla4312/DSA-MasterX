const App = {
    currentPage: null,
    _activeModalEscHandler: null,
    _lastHwState: null,
    _hwPollTimer: null,
    
    pages: {
        'home': window.HomePage,
        'library': window.LibraryPage,
        'problems': window.ProblemsPage,
        'practice': window.PracticePage,
        'dashboard': window.DashboardPage,
    },
    
    init() {
        window.addEventListener('hashchange', () => this.route());
        document.getElementById('menuToggle')?.addEventListener('click', () => this.toggleSidebar());
        
        // Setup global event listeners
        this.setupGlobalListeners();
        this.setupNetworkMonitoring();
        this.startHardwareMonitoring();
        
        this.loadSidebar();
        Icons.render();
        this.route();
    },

    setupGlobalListeners() {
        // Global code block copy delegation
        document.addEventListener('click', async (e) => {
            const copyBtn = e.target.closest('[data-action="copy-code"]');
            if (copyBtn) {
                const wrapper = copyBtn.closest('.code-block-wrapper');
                const rawCodeEl = wrapper?.querySelector('.code-block-raw code') || wrapper?.querySelector('code');
                if (rawCodeEl) {
                    await Utils.copyToClipboard(rawCodeEl.innerText, copyBtn);
                }
            }

            // Search clear button delegation
            const clearBtn = e.target.closest('.search-clear-btn');
            if (clearBtn) {
                const inputId = clearBtn.dataset.for;
                const inputEl = document.getElementById(inputId);
                if (inputEl) {
                    inputEl.value = '';
                    clearBtn.classList.remove('visible');
                    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                    inputEl.focus();
                }
            }
        });

        // Search clear button visibility tracker
        document.addEventListener('input', (e) => {
            if (e.target.matches('.search-input-wrapper .input')) {
                const wrapper = e.target.closest('.search-input-wrapper');
                const clearBtn = wrapper?.querySelector('.search-clear-btn');
                if (clearBtn) {
                    clearBtn.classList.toggle('visible', Boolean(e.target.value));
                }
            }
        });
    },

    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            App.showToast('Network connection restored', 'success');
        });
        window.addEventListener('offline', () => {
            App.showToast('You are currently offline', 'error');
        });
    },
    
    route() {
        const hash = window.location.hash.slice(2) || 'home';
        const pageName = hash.split('/')[0] || 'home';
        const params = hash.split('/').slice(1);
        
        // Update nav active state
        document.querySelectorAll('.nav-link').forEach(link => {
            const isActive = link.dataset.page === pageName || (pageName === '' && link.dataset.page === 'home');
            link.classList.toggle('active', isActive);
            link.setAttribute('aria-current', isActive ? 'page' : 'false');
        });
        
        // Cleanup previous page
        document.body.classList.remove('sidebar-hidden');
        if (this.currentPage && this.currentPage.destroy) {
            this.currentPage.destroy();
        }
        
        let page = this.pages[pageName];
        if (!page) {
            page = this.pages['home'];
            window.location.hash = '#/';
            return;
        }
        
        if (page) {
            this.currentPage = page;
            const container = document.getElementById('mainContent');
            container.className = 'main-content page-enter';
            container.innerHTML = '<div class="empty-state"><div class="skeleton" style="width: 200px; height: 24px; margin-bottom: 12px;"></div><div class="skeleton" style="width: 350px; height: 14px;"></div></div>';
            
            try {
                if (typeof page === 'function') {
                    this.currentPage = new page();
                    this.currentPage.render(container, ...params);
                } else if (page && typeof page.render === 'function') {
                    page.render(container, ...params);
                }
                Icons.render(container);
            } catch (error) {
                console.error(`Error rendering page ${pageName}:`, error);
                container.innerHTML = `
                    <div class="glass-card" style="border-color: var(--color-accent-red); margin-top: 2rem;">
                        <h2 class="heading-md" style="color: var(--color-accent-red);">${Icons.svg('x-circle', {class: 'icon-md'})} Failed to load page</h2>
                        <p class="body-sm" style="margin-top: 8px;">${Utils.escapeHtml(error.message || 'An unexpected error occurred.')}</p>
                    </div>
                `;
            }
        }
        
        // Close mobile sidebar on navigation
        document.getElementById('sidebar')?.classList.remove('open');
    },
    
    async loadSidebar() {
        try {
            // Load hardware status
            await this.updateHardwareStatus(false);

            // Load aggregate stats
            const statsContainer = document.getElementById('sidebarStats');
            if (statsContainer) {
                try {
                    const stats = await API.stats();
                    if (stats) {
                        statsContainer.innerHTML = `
                            <div class="sidebar-stat">
                                <div class="value">${stats.processed_count || 0}/${stats.total_lectures || 0}</div>
                                <div class="label">Processed</div>
                            </div>
                            <div class="sidebar-stat">
                                <div class="value">${stats.total_problems || 0}</div>
                                <div class="label">Problems</div>
                            </div>
                            <div class="sidebar-stat">
                                <div class="value">${stats.solved_count || 0}</div>
                                <div class="label">Solved</div>
                            </div>
                            <div class="sidebar-stat">
                                <div class="value">${stats.total_attempts || 0}</div>
                                <div class="label">Attempts</div>
                            </div>
                        `;
                    }
                } catch(e) {
                    console.error("Failed to load app stats", e);
                }
            }
        } catch (error) {
            console.error('Failed to load sidebar data:', error);
        }
    },

    startHardwareMonitoring() {
        // Hardware / Battery API (instant browser callbacks for power state changes)
        if (typeof navigator !== 'undefined' && navigator.getBattery) {
            navigator.getBattery().then(battery => {
                battery.addEventListener('chargingchange', () => {
                    this.updateHardwareStatus(true);
                });
                battery.addEventListener('levelchange', () => {
                    this.updateHardwareStatus(false);
                });
            }).catch(() => {});
        }

        // Fast update when user returns / focuses window
        window.addEventListener('focus', () => {
            this.updateHardwareStatus(false);
        });

        // Background polling (every 2.5s) to detect Windows AC adapter changes and power state
        if (this._hwPollTimer) clearInterval(this._hwPollTimer);
        this._hwPollTimer = setInterval(() => {
            this.updateHardwareStatus(false);
        }, 2500);
    },

    async updateHardwareStatus(forceAnimate = false) {
        const hwContainer = document.getElementById('sidebarHardware');
        if (!hwContainer) return;

        try {
            const hwData = await API.hardware();
            if (!hwData) return;

            const isBattery = hwData.device === 'battery' || hwData.plugged_in === false;
            const isHetero = hwData.device === 'heterogeneous';
            const isGpu = !isBattery && (isHetero || hwData.device === 'cuda' || (hwData.label && hwData.label.toLowerCase().includes('cuda')));
            
            const title = hwData.title || (isBattery ? '🔋 CPU Engine (Battery)' : (isHetero ? '⚡ Dual CPU + iGPU' : (isGpu ? 'GPU Acceleration' : 'CPU Engine')));
            const sub = hwData.model || (isBattery ? `${hwData.battery_percent || 0}% Battery · CPU int8` : (isHetero ? 'Intel Iris Xe · OpenVINO' : (isGpu ? 'NVIDIA CUDA · fp16' : 'Standard Mode')));
            const iconName = isBattery ? (hwData.plugged_in ? 'battery-charging' : 'battery') : (isGpu ? 'zap' : 'activity');
            const wrapperClass = isBattery ? 'battery' : (isGpu ? 'gpu' : 'cpu');
            const tooltip = hwData.label || (isBattery ? 'Battery optimization mode active' : 'Backend compute device');

            // Detect state change
            let hasChanged = false;
            let becameBattery = false;
            let becamePlugged = false;

            if (this._lastHwState) {
                if (this._lastHwState.plugged_in !== hwData.plugged_in || this._lastHwState.device !== hwData.device) {
                    hasChanged = true;
                    if (!hwData.plugged_in && this._lastHwState.plugged_in) {
                        becameBattery = true;
                    } else if (hwData.plugged_in && !this._lastHwState.plugged_in) {
                        becamePlugged = true;
                    }
                } else if (this._lastHwState.battery_percent !== hwData.battery_percent || this._lastHwState.model !== hwData.model) {
                    hasChanged = true;
                }
            }

            // Render DOM content
            const shouldAnimate = forceAnimate || (this._lastHwState && (becameBattery || becamePlugged));
            const animClass = shouldAnimate ? (isBattery ? 'pulse-battery' : 'pulse-update') : '';

            hwContainer.innerHTML = `
                <div class="hw-badge ${animClass}" title="${Utils.escapeHtml(tooltip)}">
                    <div class="hw-icon-wrapper ${wrapperClass}" aria-hidden="true">
                        ${Icons.svg(iconName, {class: 'hw-icon'})}
                    </div>
                    <div class="hw-text">
                        <span class="hw-title">${Utils.escapeHtml(title)}</span>
                        <span class="hw-sub">${Utils.escapeHtml(sub)}</span>
                    </div>
                </div>
            `;

            if (shouldAnimate) {
                const badgeEl = hwContainer.querySelector('.hw-badge');
                if (badgeEl) {
                    setTimeout(() => {
                        badgeEl.classList.remove('pulse-battery', 'pulse-update');
                    }, 700);
                }
            }

            // Notify user on transition
            if (becameBattery) {
                App.showToast(`Switched to Battery Mode: CPU int8 optimization active (${hwData.battery_percent || 0}%)`, 'info');
            } else if (becamePlugged) {
                App.showToast('AC Power connected: Heterogeneous Dual CPU + iGPU acceleration restored!', 'success');
            }

            this._lastHwState = hwData;
        } catch (e) {
            // Silently ignore transient network fetch errors during polling
        }
    },
    
    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        container.setAttribute('role', 'status');
        container.setAttribute('aria-live', 'polite');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="body-sm">${Utils.escapeHtml(message)}</span>
            <button class="toast-close" aria-label="Dismiss notification">${Icons.svg('x', {class: 'icon-sm'})}</button>
        `;
        container.appendChild(toast);
        
        let removeTimer = setTimeout(removeToast, 3500);

        function removeToast() {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 200);
        }

        // Pause on hover
        toast.addEventListener('mouseenter', () => clearTimeout(removeTimer));
        toast.addEventListener('mouseleave', () => {
            removeTimer = setTimeout(removeToast, 2000);
        });

        // Close on click
        toast.querySelector('.toast-close')?.addEventListener('click', () => {
            clearTimeout(removeTimer);
            removeToast();
        });
    },
    
    showModal(html) {
        const overlay = document.getElementById('modalOverlay');
        if (!overlay) return;
        overlay.innerHTML = html;
        overlay.style.display = 'flex';
        requestAnimationFrame(() => overlay.classList.add('active'));
        Icons.render(overlay);

        // Escape key dismiss handler
        if (this._activeModalEscHandler) {
            document.removeEventListener('keydown', this._activeModalEscHandler);
        }
        this._activeModalEscHandler = (e) => {
            if (e.key === 'Escape') {
                App.closeModal();
            }
        };
        document.addEventListener('keydown', this._activeModalEscHandler);

        // Close on overlay backdrop click
        overlay.onclick = (e) => {
            if (e.target === overlay) App.closeModal();
        };

        // Close on close button delegation
        overlay.querySelectorAll('[data-action="close-modal"]').forEach(btn => {
            btn.onclick = () => App.closeModal();
        });
    },
    
    closeModal() {
        const overlay = document.getElementById('modalOverlay');
        if (overlay) {
            overlay.classList.remove('active');
            if (this._activeModalEscHandler) {
                document.removeEventListener('keydown', this._activeModalEscHandler);
                this._activeModalEscHandler = null;
            }
            setTimeout(() => {
                overlay.style.display = 'none';
                overlay.innerHTML = '';
            }, 220);
        }
    },
    
    toggleSidebar() {
        document.getElementById('sidebar')?.classList.toggle('open');
    }
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
