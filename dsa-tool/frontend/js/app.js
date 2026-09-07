const App = {
    currentPage: null,
    _activeModalEscHandler: null,
    
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
            const hwContainer = document.getElementById('sidebarHardware');
            if (hwContainer) {
                try {
                    const hwData = await API.hardware();
                    if (hwData) {
                        const isGpu = hwData.device === 'cuda' || (hwData.label && hwData.label.toLowerCase().includes('cuda'));
                        const title = isGpu ? 'GPU Acceleration' : 'CPU Engine';
                        const sub = isGpu ? (hwData.model || 'NVIDIA CUDA · fp16') : 'Standard Mode';
                        const iconName = isGpu ? 'zap' : 'activity';
                        hwContainer.innerHTML = `
                            <div class="hw-badge" title="Backend compute device">
                                <div class="hw-icon-wrapper ${isGpu ? 'gpu' : 'cpu'}" aria-hidden="true">
                                    ${Icons.svg(iconName, {class: 'hw-icon'})}
                                </div>
                                <div class="hw-text">
                                    <span class="hw-title">${Utils.escapeHtml(title)}</span>
                                    <span class="hw-sub">${Utils.escapeHtml(sub)}</span>
                                </div>
                            </div>
                        `;
                    }
                } catch(e) {
                    console.error("Failed to load hardware stats", e);
                }
            }

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
