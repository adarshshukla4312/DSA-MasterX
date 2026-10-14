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
            const errDetail = error?.message || 'Server connection refused or offline.';
            const retryTarget = this.container;
            container.innerHTML = this.getLayoutHtml(false) + `
                <div class="glass-card flex-col gap-md" style="margin-top: 1rem; border-color: rgba(255, 32, 71, 0.3); background: rgba(255, 32, 71, 0.04); padding: 1.5rem;">
                    <div class="flex-row gap-sm" style="align-items: center;">
                        <span style="color: var(--color-accent-red);">${Icons.svg('alert-triangle', {class: 'icon-md'})}</span>
                        <h3 class="heading-sm" style="color: var(--color-accent-red); margin: 0;">Failed to Connect to GritX Backend</h3>
                    </div>
                    <p class="body-sm" style="color: var(--color-body); margin: 0;">
                        Could not retrieve lectures from the local server (<code>${Utils.escapeHtml(errDetail)}</code>).
                        Ensure the GritX engine is active on <strong>http://localhost:8000</strong>.
                    </p>
                    <div class="flex-row gap-sm" style="margin-top: 0.5rem;">
                        <button class="btn-primary" id="retryLibraryBtn" style="cursor: pointer;">
                            ${Icons.svg('refresh-cw', {class: 'icon-sm'})} Retry Connection
                        </button>
                    </div>
                </div>
            `;
            const retryBtn = container.querySelector('#retryLibraryBtn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    this.render(retryTarget);
                });
            }
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
        if (changeFolderBtn) changeFolderBtn.onclick = () => this.openFolderPickerModal();
        if (currentLectureDirEl) currentLectureDirEl.onclick = () => this.openFolderPickerModal();


        
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
            
            if (action === 'copy-terminal-logs') {
                const card = e.target.closest('.active-pipeline-card') || e.target.closest('.terminal-console');
                const logOutput = card ? card.querySelector('.log-output') : null;
                if (logOutput) {
                    const text = logOutput.innerText || logOutput.textContent || '';
                    navigator.clipboard.writeText(text).then(() => {
                        App.showToast('Terminal logs copied to clipboard', 'info');
                    }).catch(() => {
                        App.showToast('Failed to copy logs', 'error');
                    });
                }
                return;
            }

            if (action === 'clear-terminal-logs') {
                const card = e.target.closest('.active-pipeline-card') || e.target.closest('.terminal-console');
                const logOutput = card ? card.querySelector('.log-output') : null;
                if (logOutput) {
                    logOutput.innerHTML = '';
                    App.showToast('Terminal output cleared', 'info');
                }
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

        // 3. Update rich terminal metadata badges (mode, tokens, attempt, subprocess)
        const metaBadgesEl = card.querySelector('.terminal-meta-badges');
        if (metaBadgesEl) {
            metaBadgesEl.innerHTML = Components.renderTerminalBadges(jobStatus);
        }

        // 4. Smooth incremental log updates without flickering
        const logOutput = card.querySelector('.log-output');
        if (logOutput) {
            const rawLogs = jobStatus.logs || [];
            const lines = Components.formatLogLines(rawLogs);
            const isProcessing = jobStatus.status === 'processing' || jobStatus.status === 'starting';

            // Find or remove cursor
            let cursorLine = logOutput.querySelector('.terminal-active-cursor-line');

            const existingRows = logOutput.querySelectorAll('.terminal-row');
            const existingCount = existingRows.length;

            if (lines.length > existingCount) {
                const fragment = document.createDocumentFragment();
                for (let i = existingCount; i < lines.length; i++) {
                    const line = lines[i];
                    const temp = document.createElement('div');
                    temp.innerHTML = Components.renderLogRow(line);
                    const row = temp.firstElementChild;
                    if (row) {
                        row.classList.add('new-row');
                        fragment.appendChild(row);
                    }
                }
                if (cursorLine) {
                    logOutput.insertBefore(fragment, cursorLine);
                } else {
                    logOutput.appendChild(fragment);
                }
                logOutput.scrollTop = logOutput.scrollHeight;
            } else if (existingCount === 0 && lines.length > 0) {
                const html = lines.map(line => Components.renderLogRow(line)).join('');
                logOutput.innerHTML = html;
                logOutput.scrollTop = logOutput.scrollHeight;
            }

            // Prune old DOM rows if count exceeds 100 to prevent browser DOM memory leaks
            const allRows = logOutput.querySelectorAll('.terminal-row');
            if (allRows.length > 100) {
                const excess = allRows.length - 100;
                for (let r = 0; r < excess; r++) {
                    allRows[r].remove();
                }
            }

            // Maintain live pulsing terminal cursor
            cursorLine = logOutput.querySelector('.terminal-active-cursor-line');
            if (isProcessing) {
                if (!cursorLine) {
                    cursorLine = document.createElement('div');
                    cursorLine.className = 'terminal-active-cursor-line';
                    cursorLine.innerHTML = `<span class="terminal-cursor"></span> <span class="caption" style="color: #64748b; font-size: 10px;">active process</span>`;
                    logOutput.appendChild(cursorLine);
                    logOutput.scrollTop = logOutput.scrollHeight;
                }
            } else if (cursorLine) {
                cursorLine.remove();
            }
        }
    },
    
    openFolderPickerModal() {
        const cur = this._currentLectureDir || '';
        const videoCount = this._lectures ? this._lectures.length : 0;
        
        App.showModal(Components.folderPickerModal(cur, videoCount));
        
        const modalInput = document.getElementById('modalFolderInput');
        const browseBtn = document.getElementById('btnModalNativeBrowse');
        const browseText = document.getElementById('btnModalNativeBrowseText');
        const checkBtn = document.getElementById('btnModalCheckFolder');
        const feedback = document.getElementById('modalFolderFeedback');
        const saveBtn = document.getElementById('btnModalSaveFolder');

        const validatePath = async (val) => {
            if (!val || !val.trim()) {
                if (feedback) feedback.innerHTML = '<span style="color: var(--color-ash);">Enter a folder path</span>';
                return false;
            }
            try {
                const res = await API.settings.validateDir(val.trim());
                if (res.exists) {
                    if (feedback) feedback.innerHTML = `<span style="color: var(--color-accent-green); display: flex; align-items: center; gap: 4px;">${Icons.svg('check', {class: 'icon-xs'})} Valid folder &bull; Found <strong>${res.video_count}</strong> video file(s)</span>`;
                    return true;
                } else {
                    if (feedback) feedback.innerHTML = `<span style="color: var(--color-accent-red); display: flex; align-items: center; gap: 4px;">${Icons.svg('x', {class: 'icon-xs'})} ${res.error || 'Directory does not exist'}</span>`;
                    return false;
                }
            } catch (err) {
                if (feedback) feedback.innerHTML = `<span style="color: var(--color-accent-red);">${err.message || 'Validation error'}</span>`;
                return false;
            }
        };

        if (modalInput) {
            modalInput.addEventListener('input', Utils.debounce(() => {
                validatePath(modalInput.value);
            }, 350));
            modalInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (saveBtn) saveBtn.click();
                }
            });
        }

        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                validatePath(modalInput ? modalInput.value : '');
            });
        }

        if (browseBtn) {
            browseBtn.addEventListener('click', async () => {
                try {
                    browseBtn.disabled = true;
                    if (browseText) browseText.textContent = 'Waiting for selection...';
                    const res = await API.settings.browseFolder();
                    if (!res.cancelled && res.lecture_dir) {
                        this._currentLectureDir = res.lecture_dir;
                        const currentEl = document.getElementById('currentLectureDir');
                        if (currentEl) currentEl.textContent = res.lecture_dir;
                        App.closeModal();
                        if (window.Toast) Toast.success(`Folder updated! Found ${res.video_count} videos.`);
                        await API.lectures.scan();
                        this.render(this.container);
                    }
                } catch (err) {
                    if (window.Toast) Toast.error('Could not browse folder: ' + err.message);
                } finally {
                    browseBtn.disabled = false;
                    if (browseText) browseText.textContent = 'Browse on Computer...';
                }
            });
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const pathVal = modalInput ? modalInput.value.trim() : '';
                if (!pathVal) {
                    if (feedback) feedback.innerHTML = '<span style="color: var(--color-accent-red);">Please enter a folder path</span>';
                    return;
                }
                saveBtn.disabled = true;
                saveBtn.textContent = 'Saving...';
                try {
                    const res = await API.settings.setLectureDir(pathVal);
                    this._currentLectureDir = res.lecture_dir;
                    const currentEl = document.getElementById('currentLectureDir');
                    if (currentEl) currentEl.textContent = res.lecture_dir;
                    App.closeModal();
                    if (window.Toast) Toast.success(`Folder updated! Found ${res.video_count} videos.`);
                    await API.lectures.scan();
                    this.render(this.container);
                } catch (err) {
                    if (feedback) feedback.innerHTML = `<span style="color: var(--color-accent-red);">${err.message || 'Error updating folder'}</span>`;
                    saveBtn.disabled = false;
                    saveBtn.textContent = 'Save & Rescan';
                }
            });
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
