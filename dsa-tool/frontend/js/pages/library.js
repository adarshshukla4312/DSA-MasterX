window.LibraryPage = {
    _pollInterval: null,
    _processingLectureId: null,
    _lectures: [],
    _pipelineHash: '',
    _cachedJobStatuses: {},
    _clickHandler: null,
    _inFlightLectures: new Set(),
    _isProcessingAll: false,
    
    async render(container) {
        this.container = container;
        
        // Initial layout with skeletons
        container.innerHTML = this.getLayoutHtml(true);
        
        // Fetch data
        try {
            const [lecturesData, hashData, dirData] = await Promise.all([
                API.lectures.list(),
                API.pipelineHash(),
                API.settings.getLectureDir().catch(() => ({ lecture_dir: 'Not set' }))
            ]);
            
            const rawLectures = lecturesData.lectures || lecturesData || [];
            this._lectures = (Array.isArray(rawLectures) ? rawLectures : []).sort(Utils.compareLectures);
            this._pipelineHash = hashData.hash || hashData || '';
            this._currentLectureDir = dirData?.lecture_dir || 'Not configured';
            
            // Re-render layout with actual data wrappers
            this.container.innerHTML = this.getLayoutHtml(false);
            
            this.renderList();
            this.bindEvents();
            
            // If any lectures are currently processing on page load/refresh, start polling and fetch their logs immediately
            const activeJobs = this._lectures.filter(l => l.status === 'processing' || l.status === 'starting');
            if (activeJobs.length > 0) {
                activeJobs.forEach(l => this.fetchAndMountJobPanel(l.id));
                this.startPolling(null);
            }
        } catch (error) {
            console.error('Failed to load library data', error);
            container.innerHTML = this.getLayoutHtml(false) + '<div class="glass-card" style="margin-top: 1rem; border-color: var(--color-accent-red);"><p class="body-sm" style="color: var(--color-accent-red);">Failed to load lectures.</p></div>';
        }
    },
    
    getLayoutHtml(loading = false) {
        const banner = Components.heroBanner('Lecture Library', 'Manage and process your offline DSA lecture recordings with automated transcription, concept extraction, and question synthesis.', 'Course Repository');
        if (loading) {
            const skeletons = Array(5).fill(0).map(() => Components.skeletonCard()).join('');
            return `
                ${banner}
                <div class="glass-card flex-row gap-md" style="align-items: center; margin-bottom: 1.5rem; padding: 12px 20px;">
                    ${Components.skeleton('100%', '36px')}
                </div>
                <div class="flex-col gap-md">
                    ${skeletons}
                </div>
            `;
        }
        
        return `
            ${banner}
            
            <!-- Dedicated Active Processing Section at the Top -->
            <div id="activeProcessingContainer" class="active-processing-container" style="display: none;">
                <div class="active-processing-header">
                    <div class="flex-row gap-sm" style="align-items: center;">
                        <span class="processing-pulse-dot"></span>
                        <h2 class="heading-sm" style="margin: 0; color: var(--color-ink);">Currently Processing</h2>
                        <span id="activeJobBadge" class="status-pill blue">1 Active</span>
                    </div>
                </div>
                <div id="activeProcessingList" class="flex-col gap-md">
                    <!-- Processing cards render here -->
                </div>
            </div>

            <!-- Lecture Folder Selector Bar -->
            <div class="glass-card flex-row gap-md" style="align-items: center; justify-content: space-between; margin-bottom: 1rem; padding: 10px 16px; background: rgba(255,255,255,0.03);">
                <div class="flex-row gap-sm" style="align-items: center; overflow: hidden; flex: 1;">
                    <span style="color: var(--color-brand);">${Icons.svg('folder', {class: 'icon-sm'})}</span>
                    <span class="body-sm" style="color: var(--color-ash); font-weight: 500; white-space: nowrap;">Lectures Folder:</span>
                    <span id="currentLectureDir" class="code-badge" style="font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 65%; cursor: pointer;" title="Click to change lecture directory">${this._currentLectureDir || 'Detecting...'}</span>
                </div>
                <button class="btn-ghost" id="changeFolderBtn" style="flex-shrink: 0; padding: 6px 14px; font-size: 0.82rem;">Change Folder</button>
            </div>

            <div class="glass-card flex-row gap-md" style="align-items: center; margin-bottom: 1.5rem; padding: 10px 16px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 220px;">
                    ${Components.searchInput('Search by title or filename...', 'librarySearch')}
                </div>
                <div style="width: 140px; flex-shrink: 0;">
                    ${Components.select([
                        'All', 'New', 'Incomplete', 'Complete'
                    ], 'libraryStatusFilter', 'All')}
                </div>
                <button class="btn-ghost" data-action="rescan" id="rescanBtn" style="flex-shrink: 0;">${Icons.svg('refresh-cw', {class: 'icon-sm'})} Rescan</button>
                <button class="btn-primary" data-action="process-all" id="processAllBtn" style="flex-shrink: 0;">Process All</button>
            </div>
            
            <div class="body-sm" style="margin-bottom: 1rem; color: var(--color-ash);" id="lectureCount">
                Loading...
            </div>
            
            <div class="flex-col gap-md stagger-in" id="lectureList">
                <!-- Regular Lecture cards rendered here -->
            </div>
        `;
    },
    
    renderList() {
        const searchInput = document.getElementById('librarySearch');
        const statusSelect = document.getElementById('libraryStatusFilter');
        
        const query = (searchInput?.value || '').toLowerCase().trim();
        const statusFilter = (statusSelect?.value || 'All').toLowerCase();
        
        // 1. Separate currently processing lectures from general list
        const processingLectures = this._lectures.filter(l => l.status === 'processing' || l.status === 'starting' || l.status === 'cancelling');
        const regularLectures = this._lectures.filter(l => !processingLectures.some(p => p.id === l.id));
        
        // Render Active Processing Section
        const activeContainer = document.getElementById('activeProcessingContainer');
        const activeList = document.getElementById('activeProcessingList');
        const activeBadge = document.getElementById('activeJobBadge');
        
        if (activeContainer && activeList) {
            if (processingLectures.length > 0) {
                activeContainer.style.display = 'block';
                if (activeBadge) {
                    activeBadge.textContent = `${processingLectures.length} Active`;
                }
                
                // Render dedicated active pipeline command cards
                activeList.innerHTML = processingLectures.map(l => {
                    const cachedStatus = this._cachedJobStatuses[l.id] || { progress: 0, step_name: 'Starting pipeline...', status: l.status };
                    return Components.activePipelineCard(cachedStatus, l);
                }).join('');
                
                // Fetch latest job status for each active lecture
                processingLectures.forEach(l => {
                    this.fetchAndMountJobPanel(l.id);
                });
            } else {
                activeContainer.style.display = 'none';
            }
        }
        
        // Filter regular lectures
        const filtered = regularLectures.filter(l => {
            const matchQuery = Utils.matchLecture(l, query);
            const status = (l.status || 'new').toLowerCase();
            let matchStatus = true;
            if (statusFilter === 'new') {
                matchStatus = status === 'new';
            } else if (statusFilter === 'incomplete') {
                matchStatus = status !== 'completed' && status !== 'new';
            } else if (statusFilter === 'complete' || statusFilter === 'completed') {
                matchStatus = status === 'completed';
            }
            return matchQuery && matchStatus;
        });
        
        const listContainer = document.getElementById('lectureList');
        const countContainer = document.getElementById('lectureCount');
        
        if (listContainer) {
            if (filtered.length === 0) {
                listContainer.innerHTML = Components.emptyState(Icons.svg('inbox', {style: 'width: 48px; height: 48px;'}), 'No lectures found matching your criteria.');
            } else {
                listContainer.innerHTML = filtered.map(l => Components.lectureCard(l, this._pipelineHash)).join('');
            }
        }
        
        if (countContainer) {
            countContainer.textContent = `Showing ${filtered.length} of ${this._lectures.length} lectures`;
        }
        
        // Update Process All button count (clean text, no icon)
        const processAllBtn = document.getElementById('processAllBtn');
        if (processAllBtn) {
            const unprocessed = this._lectures.filter(l => l.status === 'new').length;
            processAllBtn.textContent = `Process All (${unprocessed})`;
            processAllBtn.disabled = unprocessed === 0;
        }
    },
    
    async fetchAndMountJobPanel(lectureId) {
        try {
            const jobStatus = await API.lectures.jobStatus(lectureId);
            this._cachedJobStatuses[lectureId] = jobStatus;
            this.updateJobPanel(lectureId, jobStatus);
        } catch (e) {
            console.error('Failed to fetch job panel for lecture:', lectureId, e);
        }
    },
    
    bindEvents() {
        const searchInput = document.getElementById('librarySearch');
        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce(() => this.renderList(), 250));
        }
        
        const statusSelect = document.getElementById('libraryStatusFilter');
        if (statusSelect) {
            statusSelect.addEventListener('change', () => this.renderList());
        }
        
        const changeFolderBtn = document.getElementById('changeFolderBtn');
        const currentLectureDirEl = document.getElementById('currentLectureDir');
        const handleChangeFolder = async () => {
            const cur = this._currentLectureDir || '';
            const newPath = prompt('Enter the full path to your DSA lecture videos folder on this computer:\n(e.g. D:\\Videos\\DSA or C:\\Java DSA)', cur);
            if (newPath && newPath.trim() && newPath.trim() !== cur) {
                try {
                    const res = await API.settings.setLectureDir(newPath.trim());
                    this._currentLectureDir = res.lecture_dir;
                    if (currentLectureDirEl) currentLectureDirEl.textContent = res.lecture_dir;
                    if (window.Toast) Toast.success(`Folder updated! Found ${res.video_count} videos.`);
                    await API.lectures.scan();
                    this.render(this.container);
                } catch (err) {
                    alert(err.message || 'Failed to update folder. Please verify the folder path exists.');
                }
            }
        };
        if (changeFolderBtn) changeFolderBtn.onclick = handleChangeFolder;
        if (currentLectureDirEl) currentLectureDirEl.onclick = handleChangeFolder;

        
        // Remove previous click listener if exists on container to prevent stacking
        if (this._clickHandler && this.container) {
            this.container.removeEventListener('click', this._clickHandler);
        }

        this._clickHandler = async (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            
            const action = btn.dataset.action;
            
            if (action === 'toggle-log') {
                const id = btn.dataset.id;
                const container = document.getElementById(`logContainer-${id}`);
                const chevron = btn.querySelector('.toggle-chevron');
                const textSpan = btn.querySelector('.toggle-log-text');
                if (container) {
                    const isCollapsed = container.classList.toggle('collapsed');
                    btn.setAttribute('aria-expanded', String(!isCollapsed));
                    if (textSpan) textSpan.textContent = isCollapsed ? 'Show Logs' : 'Hide Logs';
                    if (chevron) chevron.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
                }
                return;
            }
            
            if (action === 'rescan') {
                await this.handleRescan(btn);
                return;
            }
            
            if (action === 'process-all') {
                await this.handleProcessAll(btn);
                return;
            }
            
            // For individual lecture buttons
            const card = e.target.closest('.lecture-card');
            const id = btn.dataset.id || (card ? card.dataset.lectureId : null);
            
            if (['process', 'reprocess', 'extract', 'rerun'].includes(action)) {
                if (!id) return;
                const skipTranscription = (action === 'extract' || action === 'reprocess' || action === 'rerun');
                await this.handleProcessLecture(id, skipTranscription, btn);
            } else if (action === 'cancel') {
                const cancelId = id || this._processingLectureId;
                if (cancelId) {
                    await this.handleCancelLecture(cancelId);
                }
            }
        };
        
        if (this.container) {
            this.container.addEventListener('click', this._clickHandler);
        }
    },
    
    async handleRescan(btn) {
        Utils.setButtonLoading(btn, true);
        try {
            await API.lectures.scan();
            App.showToast('Scan completed successfully', 'success');
            await this.refreshData();
        } catch (e) {
            App.showToast('Lecture directory scan failed', 'error');
        } finally {
            Utils.setButtonLoading(btn, false);
            btn.innerHTML = `${Icons.svg('refresh-cw', {class: 'icon-sm'})} Rescan`;
        }
    },
    
    async handleProcessAll(btn) {
        if (btn && btn.disabled) return;
        if (this._isProcessingAll) return;
        this._isProcessingAll = true;

        if (btn) {
            Utils.setButtonLoading(btn, true);
            btn.disabled = true;
        }
        try {
            const res = await API.lectures.processAll();
            if (res.message) {
                App.showToast(res.message, 'info');
            } else {
                App.showToast('Started processing all new lectures', 'success');
            }
            await this.refreshData();
            this.startPolling(null);
        } catch (e) {
            App.showToast('Failed to start batch processing', 'error');
        } finally {
            if (btn) Utils.setButtonLoading(btn, false);
            setTimeout(() => { this._isProcessingAll = false; }, 1500);
        }
    },
    
    async handleProcessLecture(id, skipTranscription, btn = null) {
        if (!id) return;
        if (this._inFlightLectures.has(id)) {
            console.warn(`[Library] Processing request already in flight for ${id}`);
            return;
        }
        this._inFlightLectures.add(id);

        if (btn) {
            Utils.setButtonLoading(btn, true);
            btn.disabled = true;
            btn.style.pointerEvents = 'none';
        }
        
        // 1. Smooth Anime.js transition on source card
        const card = document.querySelector(`.lecture-card[data-lecture-id="${id}"]`);
        if (card && window.anime) {
            try {
                await anime({
                    targets: card,
                    translateY: -24,
                    opacity: [1, 0],
                    scale: [1, 0.96],
                    duration: 220,
                    easing: 'easeOutQuad'
                }).finished;
            } catch (err) {
                // Ignore animation interrupt
            }
        }
        
        try {
            const res = await API.lectures.process(id, skipTranscription);
            if (res && res.status === 'already_running') {
                App.showToast('Lecture processing is already running', 'info');
            } else {
                App.showToast('Started processing lecture pipeline', 'info');
            }
            
            const index = this._lectures.findIndex(l => l.id === id);
            if (index !== -1) {
                this._lectures[index].status = 'processing';
            }
            
            // Re-render list to immediately place the card into the Active Processing section at the top
            this.renderList();
            
            // Smoothly scroll to top so the active processing card is immediately front-and-center
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            // Animate active processing section entry
            const activeContainer = document.getElementById('activeProcessingContainer');
            if (activeContainer && window.anime) {
                anime({
                    targets: activeContainer,
                    opacity: [0, 1],
                    translateY: [-16, 0],
                    duration: 350,
                    easing: 'easeOutCubic'
                });
            }
            
            this.startPolling(id);
        } catch (err) {
            App.showToast('Failed to start lecture processing: ' + (err.message || ''), 'error');
            if (btn) {
                Utils.setButtonLoading(btn, false);
                btn.disabled = false;
                btn.style.pointerEvents = 'auto';
            }
        } finally {
            setTimeout(() => {
                this._inFlightLectures.delete(id);
            }, 1500);
        }
    },
    
    async handleCancelLecture(id) {
        const lecture = this._lectures.find(l => l.id === id) || { title: 'this lecture' };
        
        App.showModal(Components.cancelConfirmModal(lecture.title, id));
        
        const confirmBtn = document.getElementById('confirmCancelBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', async () => {
                App.closeModal();
                try {
                    await API.lectures.cancel(id);
                    App.showToast('Cancelled processing job', 'info');
                    delete this._cachedJobStatuses[id];
                    setTimeout(() => this.refreshData(), 800);
                } catch (err) {
                    App.showToast('Failed to cancel job', 'error');
                }
            });
        }
    },
    
    async refreshData() {
        try {
            const lecturesData = await API.lectures.list();
            const rawLectures = lecturesData.lectures || lecturesData || [];
            this._lectures = (Array.isArray(rawLectures) ? rawLectures : []).sort(Utils.compareLectures);
            this.renderList();
        } catch (error) {
            console.error('Failed to refresh data', error);
        }
    },
    
    startPolling(id) {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
        }
        
        if (id) {
            this._processingLectureId = id;
        }
        
        this._pollInterval = setInterval(async () => {
            let processingIds = [];
            if (this._processingLectureId) {
                processingIds.push(this._processingLectureId);
            } else {
                processingIds = this._lectures.filter(l => l.status === 'processing' || l.status === 'starting').map(l => l.id);
            }
            
            if (processingIds.length === 0) {
                clearInterval(this._pollInterval);
                return;
            }
            
            for (const pid of processingIds) {
                try {
                    const jobStatus = await API.lectures.jobStatus(pid);
                    this._cachedJobStatuses[pid] = jobStatus;
                    const status = jobStatus.status;
                    
                    this.updateJobPanel(pid, jobStatus);
                    
                    if (['completed', 'error', 'cancelled'].includes(status)) {
                        if (this._processingLectureId === pid) {
                            this._processingLectureId = null;
                        }
                        delete this._cachedJobStatuses[pid];
                        
                        setTimeout(() => this.refreshData(), 1200);
                        
                        if (!this._processingLectureId && processingIds.length <= 1) {
                            clearInterval(this._pollInterval);
                        }
                    }
                } catch (e) {
                    console.error('Error polling job status', e);
                }
            }
        }, 2000);
    },
    
    updateJobPanel(lectureId, jobStatus) {
        let card = document.querySelector(`.active-pipeline-card[data-lecture-id="${Utils.escapeHtml(lectureId)}"]`);
        if (!card) {
            // Check if active processing section needs re-rendering
            const activeContainer = document.getElementById('activeProcessingContainer');
            if (activeContainer && activeContainer.style.display !== 'block') {
                this.renderList();
                return;
            }
            card = document.querySelector(`.active-pipeline-card[data-lecture-id="${Utils.escapeHtml(lectureId)}"]`);
            if (!card) return;
        }

        const progress = Math.round(jobStatus.progress || 0);
        const stepName = jobStatus.step_name || 'Processing pipeline...';

        // 1. Smoothly update step text and percentage
        const stepTextEl = card.querySelector('.pipeline-current-step-text');
        if (stepTextEl && stepTextEl.textContent !== stepName) {
            stepTextEl.textContent = stepName;
        }

        const progressPercEl = card.querySelector('.pipeline-progress-percentage');
        if (progressPercEl) {
            progressPercEl.textContent = `${progress}%`;
        }

        const progressFillEl = card.querySelector('.progress-bar-fill');
        if (progressFillEl) {
            progressFillEl.style.width = `${progress}%`;
        }

        // 2. Update visual 3-segment pipeline stepper
        let currentStep = 1;
        const sLower = stepName.toLowerCase();
        if (sLower.includes('extract') || sLower.includes('concept')) {
            currentStep = 2;
        } else if (sLower.includes('identif') || sLower.includes('match') || sLower.includes('mcq') || sLower.includes('complete')) {
            currentStep = 3;
        }

        for (let i = 1; i <= 3; i++) {
            const stepItem = card.querySelector(`.pipeline-step-item[data-step="${i}"]`);
            if (stepItem) {
                stepItem.classList.remove('active', 'completed');
                const numSpan = stepItem.querySelector('.step-num');
                if (currentStep === i) {
                    stepItem.classList.add('active');
                    if (numSpan) numSpan.textContent = String(i);
                } else if (currentStep > i) {
                    stepItem.classList.add('completed');
                    if (numSpan && !numSpan.querySelector('svg')) {
                        numSpan.innerHTML = Icons.svg('check', {class: 'icon-xs'});
                    }
                } else {
                    if (numSpan) numSpan.textContent = String(i);
                }
            }

            const connector = card.querySelector(`.pipeline-step-connector[data-connector="${i}"]`);
            if (connector) {
                connector.classList.toggle('completed', currentStep > i);
            }
        }

        // 3. Smooth incremental log updates without flickering
        const logOutput = card.querySelector('.log-output');
        if (logOutput) {
            const rawLogs = jobStatus.logs || [];
            const lines = Components.formatLogLines(rawLogs);
            const existingRows = logOutput.querySelectorAll('.terminal-row');
            const existingCount = existingRows.length;

            if (lines.length > existingCount) {
                const fragment = document.createDocumentFragment();
                for (let i = existingCount; i < lines.length; i++) {
                    const line = lines[i];
                    const row = document.createElement('div');
                    row.className = 'terminal-row new-row';
                    const timeMatch = line.match(/^(\[\d{2}:\d{2}:\d{2}\])\s*(.*)$/);
                    if (timeMatch) {
                        row.innerHTML = `<span class="log-timestamp">${Utils.escapeHtml(timeMatch[1])}</span> <span class="log-text">${Utils.escapeHtml(timeMatch[2])}</span>`;
                    } else {
                        row.innerHTML = `<span class="log-text">${Utils.escapeHtml(line)}</span>`;
                    }
                    fragment.appendChild(row);
                }
                logOutput.appendChild(fragment);
                logOutput.scrollTop = logOutput.scrollHeight;
            } else if (existingCount === 0 && lines.length > 0) {
                const html = lines.map(line => {
                    const timeMatch = line.match(/^(\[\d{2}:\d{2}:\d{2}\])\s*(.*)$/);
                    if (timeMatch) {
                        return `<div class="terminal-row"><span class="log-timestamp">${Utils.escapeHtml(timeMatch[1])}</span> <span class="log-text">${Utils.escapeHtml(timeMatch[2])}</span></div>`;
                    }
                    return `<div class="terminal-row"><span class="log-text">${Utils.escapeHtml(line)}</span></div>`;
                }).join('');
                logOutput.innerHTML = html;
                logOutput.scrollTop = logOutput.scrollHeight;
            }
        }
    },
    
    destroy() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
            this._pollInterval = null;
        }
        if (this._clickHandler && this.container) {
            this.container.removeEventListener('click', this._clickHandler);
            this._clickHandler = null;
        }
        this._processingLectureId = null;
        this._cachedJobStatuses = {};
        this._inFlightLectures.clear();
        this._isProcessingAll = false;
        this.container = null;
    }
};
