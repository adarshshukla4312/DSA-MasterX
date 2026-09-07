const ProblemsPage = {
    _container: null,
    _lectures: [],
    _selectedLectureId: null,
    _selectedProblemIndex: null, // null = show lecture overview; number = show specific question in focus mode
    _viewMode: 'lecture_overview', // 'lecture_overview' | 'question_detail'
    _searchQuery: '',
    _lectureDataCache: {},
    _solvedIds: new Set(),
    _keydownHandler: null,

    async render(container) {
        this._container = container;
        
        container.innerHTML = `
            ${Components.heroBanner('Identified Problems', 'Explore verified algorithmic problems, core intuition breakdowns, and reconstructed Java solutions extracted directly from course lectures.', 'Problem Intelligence')}
            <div class="two-panel">
                <div class="panel-left glass-card" style="padding: 0; overflow: hidden; display: flex; flex-direction: column;" id="problemsLeftPanel">
                    <div class="problems-left-header" id="problemsLeftHeader">
                        ${Components.skeleton('100%', '36px')}
                    </div>
                    <div style="flex: 1; overflow-y: auto;" id="problemsNavContainer">
                        <div style="padding: 1rem; display: flex; flex-direction: column; gap: 8px;">
                            ${Components.skeletonCard()}
                            ${Components.skeletonCard()}
                            ${Components.skeletonCard()}
                        </div>
                    </div>
                </div>

                <div class="panel-right" id="problemList">
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        ${Components.skeletonCard()}
                        ${Components.skeletonCard()}
                    </div>
                </div>
            </div>
        `;

        try {
            const [lecturesRes, solvedRes] = await Promise.all([
                API.lectures.list(),
                API.problems.solved().catch(() => ({ solved_ids: [] }))
            ]);

            this._lectures = (lecturesRes || [])
                .filter(l => ['identified', 'matched', 'extracted', 'completed'].includes(l.status))
                .sort(Utils.compareLectures);

            if (solvedRes && solvedRes.solved_ids) {
                this._solvedIds = new Set(solvedRes.solved_ids);
            } else if (Array.isArray(solvedRes)) {
                this._solvedIds = new Set(solvedRes);
            }

            if (this._lectures.length === 0) {
                container.innerHTML = `
                    ${Components.pageHeader('Identified Problems', 'Review extracted algorithmic problems, verbal explanations, reconstructed Java solutions, and matched LeetCode challenges.', 'green', 'Algorithmic Problem Explorer', 'code-2')}
                    ${Components.emptyState(Icons.svg('code-2', {class: 'icon-xl', style: 'width: 32px; height: 32px;'}), 'No identified problems yet. Process lectures in the Lecture Library first.')}
                `;
                return;
            }

            // Pre-fetch problem counts for badges
            await this._preloadProblemCounts();

            if (!this._selectedLectureId || !this._lectures.find(l => l.id === this._selectedLectureId)) {
                this._selectedLectureId = this._lectures[0].id;
            }

            this._viewMode = 'lecture_overview';
            this._selectedProblemIndex = null;

            this._renderLeftPanel(false);
            await this._renderRightPanel(false);
            this._bindEvents();

        } catch (error) {
            console.error('Failed to load problems data', error);
            container.innerHTML = Components.emptyState(
                Icons.svg('x-circle', {style: 'width: 48px; height: 48px;'}),
                'Failed to load problems: ' + error.message
            );
        }
    },

    destroy() {
        if (this._keydownHandler) {
            window.removeEventListener('keydown', this._keydownHandler);
            this._keydownHandler = null;
        }
        this._container = null;
    },

    async _preloadProblemCounts() {
        const promises = this._lectures.map(async (l) => {
            if (Array.isArray(l.problems_discussed)) {
                l._problemCount = l.problems_discussed.length;
            } else {
                try {
                    const data = await API.lectures.get(l.id);
                    l._problemCount = (data.problems_discussed || []).length;
                    this._lectureDataCache[l.id] = { lecture: data, matches: null };
                } catch {
                    l._problemCount = 0;
                }
            }
        });
        await Promise.all(promises);
    },

    _bindEvents() {
        if (!this._container) return;

        // Container-level click delegation
        this._container.addEventListener('click', async (e) => {
            // 1. Lecture Card in Left Panel (Mode 1)
            const lectureCard = e.target.closest('.lecture-nav-card');
            if (lectureCard) {
                const id = lectureCard.dataset.id;
                if (id && id !== this._selectedLectureId) {
                    await this._selectLecture(id);
                }
                return;
            }

            // 2. Problem Overview Card on Right (Mode 1 -> Mode 2)
            const problemOverviewCard = e.target.closest('.problem-overview-card');
            if (problemOverviewCard) {
                const index = parseInt(problemOverviewCard.dataset.problemIndex, 10);
                if (!isNaN(index)) {
                    await this._selectProblem(index);
                }
                return;
            }

            // 3. Back to All Lectures Button (Mode 2 -> Mode 1)
            const backBtn = e.target.closest('[data-action="back-to-lectures"]');
            if (backBtn) {
                await this._backToLectures();
                return;
            }

            // 4. Question Nav Item in Left Panel (Detail Mode)
            const questionNavItem = e.target.closest('.question-nav-item');
            if (questionNavItem) {
                const idx = parseInt(questionNavItem.dataset.problemIndex, 10);
                if (!isNaN(idx) && idx !== this._selectedProblemIndex) {
                    await this._selectProblem(idx);
                }
                return;
            }

            // 5. Prev Problem Button
            const prevBtn = e.target.closest('[data-action="prev-problem"]');
            if (prevBtn && this._selectedProblemIndex !== null && this._selectedProblemIndex > 0) {
                await this._selectProblem(this._selectedProblemIndex - 1);
                return;
            }

            // 6. Next Problem Button
            const nextBtn = e.target.closest('[data-action="next-problem"]');
            if (nextBtn && this._selectedProblemIndex !== null) {
                const currentData = this._lectureDataCache[this._selectedLectureId];
                const total = currentData?.lecture?.problems_discussed?.length || 0;
                if (this._selectedProblemIndex < total - 1) {
                    await this._selectProblem(this._selectedProblemIndex + 1);
                }
                return;
            }

            // 7. Back to Lecture Overview Button (from detail footer)
            const backOverviewBtn = e.target.closest('[data-action="back-to-overview"]');
            if (backOverviewBtn) {
                await this._backToOverview();
                return;
            }

            // 8. Toggle Solved Button
            const solvedBtn = e.target.closest('[data-action="toggle-solved"]');
            if (solvedBtn) {
                this._toggleSolved(solvedBtn);
                return;
            }

            // 9. Toggle Stage Accordion
            const stageToggleBtn = e.target.closest('[data-action="toggle-stage"]');
            if (stageToggleBtn) {
                const targetId = stageToggleBtn.dataset.target;
                const body = document.getElementById(targetId);
                const box = stageToggleBtn.closest('.checklist-stage-box');
                if (body && box) {
                    const isClosed = body.style.display === 'none';
                    body.style.display = isClosed ? 'block' : 'none';
                    box.classList.toggle('open', isClosed);
                }
                return;
            }

            // 10. Toggle All Stages
            const toggleAllBtn = e.target.closest('[data-action="toggle-all-stages"]');
            if (toggleAllBtn) {
                const scope = toggleAllBtn.dataset.scope;
                const card = document.getElementById(`checklistCard-${scope}`);
                if (card) {
                    const boxes = card.querySelectorAll('.checklist-stage-box');
                    const anyClosed = Array.from(boxes).some(b => !b.classList.contains('open'));
                    boxes.forEach(b => {
                        const body = b.querySelector('.stage-accordion-body');
                        if (anyClosed) {
                            b.classList.add('open');
                            if (body) body.style.display = 'block';
                        } else {
                            b.classList.remove('open');
                            if (body) body.style.display = 'none';
                        }
                    });
                }
                return;
            }

            // 11. Reset Checklist
            const resetBtn = e.target.closest('[data-action="reset-checklist"]');
            if (resetBtn) {
                const scope = resetBtn.dataset.scope;
                const card = document.getElementById(`checklistCard-${scope}`);
                if (card) {
                    const checkboxes = card.querySelectorAll('.methodology-checkbox');
                    checkboxes.forEach(cb => {
                        const item = cb.dataset.item;
                        localStorage.removeItem(`dsa_chk_${scope}_${item}`);
                        cb.checked = false;
                        cb.closest('.checklist-item-row')?.classList.remove('checked-row');
                    });
                    this._updateChecklistProgress(scope);
                    App.showToast('Checklist reset', 'info');
                }
                return;
            }

            // 12. Toggle Interview Verbal Mode
            const verbalBtn = e.target.closest('[data-action="toggle-verbal-mode"]');
            if (verbalBtn) {
                const scope = verbalBtn.dataset.scope;
                const card = document.getElementById(`checklistCard-${scope}`);
                if (card) {
                    const bonusStage = card.querySelector('.bonus-stage');
                    if (bonusStage) {
                        const body = bonusStage.querySelector('.stage-accordion-body');
                        bonusStage.classList.add('open', 'verbal-highlight');
                        if (body) body.style.display = 'block';
                        bonusStage.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        App.showToast('Live Interview Verbal Protocol highlighted!', 'info');
                    }
                }
                return;
            }

            // 13. Methodology Checkbox Click
            const mCheckbox = e.target.closest('.methodology-checkbox');
            if (mCheckbox) {
                const scope = mCheckbox.dataset.scope;
                const item = mCheckbox.dataset.item;
                const key = `dsa_chk_${scope}_${item}`;
                if (mCheckbox.checked) {
                    localStorage.setItem(key, '1');
                    mCheckbox.closest('.checklist-item-row')?.classList.add('checked-row');
                } else {
                    localStorage.removeItem(key);
                    mCheckbox.closest('.checklist-item-row')?.classList.remove('checked-row');
                }
                this._updateChecklistProgress(scope);
                return;
            }
        });

        // Global keyboard navigation
        this._keydownHandler = (e) => {
            if (this._viewMode === 'question_detail') {
                if (e.key === 'ArrowLeft' && !e.target.matches('input, textarea')) {
                    if (this._selectedProblemIndex > 0) {
                        e.preventDefault();
                        this._selectProblem(this._selectedProblemIndex - 1);
                    }
                } else if (e.key === 'ArrowRight' && !e.target.matches('input, textarea')) {
                    const currentData = this._lectureDataCache[this._selectedLectureId];
                    const total = currentData?.lecture?.problems_discussed?.length || 0;
                    if (this._selectedProblemIndex < total - 1) {
                        e.preventDefault();
                        this._selectProblem(this._selectedProblemIndex + 1);
                    }
                } else if (e.key === 'Escape') {
                    this._backToLectures();
                }
            }
        };
        window.addEventListener('keydown', this._keydownHandler);
    },

    _renderLeftPanel(animate = true) {
        if (!this._container) return;
        const headerEl = this._container.querySelector('#problemsLeftHeader');
        const navContainer = this._container.querySelector('#problemsNavContainer');
        if (!headerEl || !navContainer) return;

        if (this._viewMode === 'lecture_overview') {
            // Mode 1: Lectures List
            headerEl.innerHTML = `
                ${Components.searchInput('Search lectures...', 'problemsSearchInput')}
            `;
            const searchInput = headerEl.querySelector('#problemsSearchInput');
            if (searchInput) {
                searchInput.value = this._searchQuery;
                searchInput.addEventListener('input', Utils.debounce((e) => {
                    this._searchQuery = (e.target.value || '').toLowerCase().trim();
                    this._renderLectureList();
                }, 150));
            }
            this._renderLectureList();
        } else {
            // Mode 2: Question Navigator for current lecture
            const currentLecture = this._lectures.find(l => l.id === this._selectedLectureId);
            const parsed = Utils.parseLectureTitle(currentLecture?.title, currentLecture?.num, currentLecture?.filename, currentLecture?.id);
            const totalProbs = currentLecture?._problemCount || 0;

            headerEl.innerHTML = `
                <button type="button" class="nav-back-btn" data-action="back-to-lectures" aria-label="Back to all lectures">
                    ${Icons.svg('arrow-left', {class: 'icon-sm'})} Back to Lectures
                </button>
                <div class="active-lecture-sidebar-card">
                    <div class="flex-row gap-xs" style="align-items: center; margin-bottom: 4px;">
                        ${parsed.numStr ? `<span class="lecture-num-pill">${parsed.numStr}</span>` : ''}
                        ${parsed.module ? `<span class="lecture-module-pill">${Utils.escapeHtml(parsed.module)}</span>` : ''}
                    </div>
                    <div class="active-lecture-sidebar-title" title="${Utils.escapeHtml(parsed.topic)}">
                        ${Utils.escapeHtml(parsed.topic)}
                    </div>
                    <div class="caption" style="font-size: 11px; margin-top: 4px; font-family: var(--font-mono);">${totalProbs} Questions Discussed</div>
                </div>
            `;

            this._renderQuestionList();
        }

        // Smooth transition on left panel items
        if (animate && typeof anime !== 'undefined') {
            anime({
                targets: navContainer.querySelectorAll('.lecture-nav-card, .question-nav-item'),
                opacity: [0, 1],
                translateX: this._viewMode === 'question_detail' ? [-10, 0] : [10, 0],
                delay: anime.stagger(20),
                duration: 220,
                easing: 'easeOutCubic'
            });
        }
    },

    _renderLectureList() {
        const navContainer = this._container?.querySelector('#problemsNavContainer');
        if (!navContainer) return;

        const filtered = this._lectures.filter(l => Utils.matchLecture(l, this._searchQuery));

        if (filtered.length === 0) {
            navContainer.innerHTML = `
                <div style="padding: 2rem 1rem; color: var(--color-ash); font-size: 13px; text-align: center;">
                    ${Icons.svg('search', {class: 'icon-lg', style: 'margin-bottom: 8px; color: var(--color-stone);'})}
                    <div>No lectures match "<strong>${Utils.escapeHtml(this._searchQuery)}</strong>"</div>
                </div>
            `;
            return;
        }

        const html = `
            <div class="lecture-nav-list">
                ${filtered.map(l => {
                    const isActive = l.id === this._selectedLectureId;
                    const parsed = Utils.parseLectureTitle(l.title, l.num, l.filename, l.id);
                    const count = l._problemCount || 0;

                    return `
                    <div class="lecture-nav-card ${isActive ? 'active' : ''}" data-id="${Utils.escapeHtml(l.id)}" tabindex="0" role="button" aria-pressed="${isActive}">
                        <div class="lecture-card-top">
                            <div class="flex-row gap-sm" style="align-items: center; min-width: 0;">
                                ${parsed.numStr ? `<span class="lecture-num-pill">${parsed.numStr}</span>` : ''}
                                ${parsed.module ? `<span class="lecture-module-pill">${Utils.escapeHtml(parsed.module)}</span>` : ''}
                            </div>
                            <span class="lecture-prob-badge">
                                ${Icons.svg('code-2', {class: 'icon-xs'})} ${count}
                            </span>
                        </div>
                        <div class="lecture-topic-title">${Utils.escapeHtml(parsed.topic)}</div>
                    </div>
                    `;
                }).join('')}
            </div>
        `;

        navContainer.innerHTML = html;
    },

    _renderQuestionList() {
        const navContainer = this._container?.querySelector('#problemsNavContainer');
        if (!navContainer) return;

        const cached = this._lectureDataCache[this._selectedLectureId];
        const problems = cached?.lecture?.problems_discussed || [];

        if (problems.length === 0) {
            navContainer.innerHTML = `<div style="padding: 1.5rem 1rem; color: var(--color-ash); font-size: 13px; text-align: center;">No problems extracted.</div>`;
            return;
        }

        const html = `
            <div class="question-nav-list">
                ${problems.map((p, idx) => {
                    const isActive = idx === this._selectedProblemIndex;
                    const numStr = String(idx + 1).padStart(2, '0');
                    const desc = p.description || `Problem ${idx + 1}`;
                    const ts = p.timestamp_range || [];

                    return `
                    <div class="question-nav-item ${isActive ? 'active' : ''}" data-problem-index="${idx}" tabindex="0" role="button" aria-pressed="${isActive}">
                        <div class="flex-row gap-sm" style="align-items: flex-start; width: 100%; min-width: 0;">
                            <span class="question-nav-index">${numStr}</span>
                            <div class="question-nav-content">
                                <div class="question-nav-title">${Utils.escapeHtml(desc)}</div>
                                ${ts.length === 2 ? `
                                <div class="question-nav-meta">
                                    ${Icons.svg('clock', {class: 'icon-xs'})} ${Utils.escapeHtml(ts[0])} — ${Utils.escapeHtml(ts[1])}
                                </div>` : ''}
                            </div>
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>
        `;

        navContainer.innerHTML = html;
    },

    async _selectLecture(id) {
        if (this._selectedLectureId === id && this._viewMode === 'lecture_overview') return;
        this._selectedLectureId = id;
        this._viewMode = 'lecture_overview';
        this._selectedProblemIndex = null;

        // Smoothly update active indicator on left panel without re-rendering DOM
        const prevActive = this._container?.querySelector('.lecture-nav-card.active');
        if (prevActive) prevActive.classList.remove('active');
        const newActive = this._container?.querySelector(`.lecture-nav-card[data-id="${id}"]`);
        if (newActive) newActive.classList.add('active');

        this._updateHeader();
        await this._renderRightPanel(true, 'fade');
    },

    async _selectProblem(index) {
        const wasInDetail = this._viewMode === 'question_detail';
        this._viewMode = 'question_detail';
        this._selectedProblemIndex = index;

        if (!wasInDetail) {
            // Mode 1 -> Mode 2 transition: Animate left panel into question list
            this._renderLeftPanel(true);
        } else {
            // Already in Mode 2: Just update active classes in left sidebar seamlessly
            const items = this._container?.querySelectorAll('.question-nav-item');
            if (items) {
                items.forEach((item, i) => {
                    item.classList.toggle('active', i === index);
                });
                const activeItem = items[index];
                if (activeItem) {
                    activeItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        }

        this._updateHeader();
        await this._renderRightPanel(true, wasInDetail ? 'crossfade' : 'slide');
    },

    async _backToLectures() {
        this._viewMode = 'lecture_overview';
        this._selectedProblemIndex = null;

        this._renderLeftPanel(true);
        this._updateHeader();
        await this._renderRightPanel(true, 'slideBack');
    },

    async _backToOverview() {
        this._viewMode = 'lecture_overview';
        this._selectedProblemIndex = null;

        this._renderLeftPanel(true);
        this._updateHeader();
        await this._renderRightPanel(true, 'slideBack');
    },

    async _renderRightPanel(animate = true, transitionType = 'fade') {
        const rightPanel = this._container?.querySelector('#problemList');
        if (!rightPanel || !this._selectedLectureId) return;

        // Optional smooth fade out before content swap if animating
        if (animate && typeof anime !== 'undefined' && rightPanel.children.length > 0) {
            try {
                await anime({
                    targets: rightPanel.children,
                    opacity: [1, 0],
                    translateY: [0, -6],
                    duration: 100,
                    easing: 'easeInQuad'
                }).finished;
            } catch (err) {}
        }

        try {
            let lecture, matches;
            if (this._lectureDataCache[this._selectedLectureId]) {
                ({ lecture, matches } = this._lectureDataCache[this._selectedLectureId]);
                if (!matches) {
                    matches = await API.lectures.matches(this._selectedLectureId).catch(() => []);
                    this._lectureDataCache[this._selectedLectureId].matches = matches;
                }
            } else {
                [lecture, matches] = await Promise.all([
                    API.lectures.get(this._selectedLectureId),
                    API.lectures.matches(this._selectedLectureId).catch(() => [])
                ]);
                this._lectureDataCache[this._selectedLectureId] = { lecture, matches };
            }

            const problems = lecture.problems_discussed || [];
            const parsed = Utils.parseLectureTitle(lecture.title, lecture.num, lecture.filename, lecture.id);

            if (problems.length === 0) {
                rightPanel.innerHTML = Components.emptyState(
                    Icons.svg('inbox', {style: 'width: 48px; height: 48px;'}),
                    `No problems were identified in "${parsed.fullTitle}".`
                );
                return;
            }

            if (this._viewMode === 'lecture_overview') {
                // ── Mode 1: Lecture Overview (All Questions Grid) ─────────
                let html = `
                <div class="lecture-overview-banner">
                    <div class="lecture-overview-header">
                        <div>
                            <div class="flex-row gap-sm" style="align-items: center; margin-bottom: 4px;">
                                ${parsed.numStr ? `<span class="lecture-num-pill">${parsed.numStr}</span>` : ''}
                                ${parsed.module ? `<span class="lecture-module-pill">${Utils.escapeHtml(parsed.module)}</span>` : ''}
                            </div>
                            <h2 class="lecture-overview-title">${Utils.escapeHtml(parsed.topic)}</h2>
                            <div class="lecture-overview-meta">
                                <span class="tag-pill" style="color: var(--color-accent-green); border-color: rgba(17,255,153,0.3); background: rgba(17,255,153,0.06);">
                                    ${Icons.svg('code-2', {class: 'icon-xs'})} ${problems.length} Problem${problems.length > 1 ? 's' : ''} Identified
                                </span>
                                ${Array.isArray(lecture.topics) && lecture.topics.length ? lecture.topics.slice(0, 3).map(t => `<span class="tag-pill">${Utils.escapeHtml(t)}</span>`).join('') : ''}
                            </div>
                        </div>
                    </div>
                    <div class="lecture-overview-hint">
                        ${Icons.svg('info', {class: 'icon-xs', style: 'color: var(--color-accent-blue); flex-shrink: 0;'})}
                        <span>Click any problem card below to expand the complete verbal explanation, core trick, and code reconstruction.</span>
                    </div>
                </div>

                <div class="stagger-in" style="display: flex; flex-direction: column; gap: 0.65rem;">
                `;

                problems.forEach((p, idx) => {
                    let match = null;
                    if (matches && matches.length > 0) {
                        match = matches.find(m => m.problem_id === p.matched_problem_id) || matches[idx];
                    }
                    html += Components.problemOverviewCard(p, idx, match);
                });

                html += `</div>`;
                rightPanel.innerHTML = html;

            } else {
                // ── Mode 2: Question Detail & Code Focus View ─────────────
                const pIdx = this._selectedProblemIndex !== null ? this._selectedProblemIndex : 0;
                const problem = problems[pIdx] || problems[0];
                
                let match = null;
                if (matches && matches.length > 0) {
                    match = matches.find(m => m.problem_id === problem.matched_problem_id) || matches[pIdx];
                }

                const probId = match?.problem_id || `${this._selectedLectureId}-p${pIdx}`;
                const isSolved = this._solvedIds.has(probId);

                rightPanel.innerHTML = Components.problemDetailView(
                    problem,
                    pIdx,
                    problems.length,
                    lecture,
                    match,
                    isSolved
                );
            }

            // Restore saved checklist states & calculate progress
            this._restoreAllChecklists();

            // Silky Smooth Cinematic Animation on incoming content
            if (animate && typeof anime !== 'undefined') {
                if (transitionType === 'slide') {
                    anime({
                        targets: rightPanel.querySelectorAll('.problem-detail-container > *, .lecture-overview-banner, .problem-overview-card'),
                        opacity: [0, 1],
                        translateX: [14, 0],
                        duration: 240,
                        delay: anime.stagger(30),
                        easing: 'easeOutCubic'
                    });
                } else if (transitionType === 'slideBack') {
                    anime({
                        targets: rightPanel.querySelectorAll('.lecture-overview-banner, .problem-overview-card'),
                        opacity: [0, 1],
                        translateX: [-14, 0],
                        duration: 240,
                        delay: anime.stagger(30),
                        easing: 'easeOutCubic'
                    });
                } else {
                    anime({
                        targets: rightPanel.querySelectorAll('.problem-overview-card, .problem-detail-container > *, .lecture-overview-banner'),
                        opacity: [0, 1],
                        translateY: [8, 0],
                        delay: anime.stagger(25),
                        duration: 200,
                        easing: 'easeOutQuad'
                    });
                }
            }

        } catch (error) {
            console.error('Failed to load lecture details', error);
            rightPanel.innerHTML = Components.emptyState(
                Icons.svg('x-circle', {style: 'width: 48px; height: 48px;'}),
                'Failed to load problems: ' + error.message
            );
        }
    },

    _restoreChecklist(scope) {
        const card = document.getElementById(`checklistCard-${scope}`);
        if (!card) return;

        const checkboxes = card.querySelectorAll('.methodology-checkbox');
        checkboxes.forEach(cb => {
            const item = cb.dataset.item;
            const key = `dsa_chk_${scope}_${item}`;
            const saved = localStorage.getItem(key);
            if (saved === '1' || saved === 'true') {
                cb.checked = true;
                cb.closest('.checklist-item-row')?.classList.add('checked-row');
            } else {
                cb.checked = false;
                cb.closest('.checklist-item-row')?.classList.remove('checked-row');
            }
        });

        this._updateChecklistProgress(scope);
    },

    _restoreAllChecklists() {
        document.querySelectorAll('.methodology-checklist-card').forEach(card => {
            const scope = card.dataset.scope;
            if (scope) {
                this._restoreChecklist(scope);
            }
        });
    },

    _updateChecklistProgress(scope) {
        const card = document.getElementById(`checklistCard-${scope}`);
        if (!card) return;

        const allCheckboxes = card.querySelectorAll('.methodology-checkbox');
        const total = allCheckboxes.length;
        let checkedCount = 0;

        const stageBoxes = card.querySelectorAll('.checklist-stage-box');
        let completedStagesCount = 0;
        const totalStages = stageBoxes.length;

        stageBoxes.forEach(stageBox => {
            const stageId = stageBox.dataset.stageId;
            const stageCbs = stageBox.querySelectorAll('.methodology-checkbox');
            const stageTotal = stageCbs.length;
            let stageChecked = 0;

            stageCbs.forEach(cb => {
                if (cb.checked) {
                    stageChecked++;
                    checkedCount++;
                }
            });

            const chip = card.querySelector(`#stageChip-${scope}-${stageId}`);
            if (chip) {
                chip.textContent = `${stageChecked}/${stageTotal}`;
                if (stageTotal > 0 && stageChecked === stageTotal) {
                    chip.classList.add('all-checked');
                    stageBox.classList.add('completed-stage');
                    completedStagesCount++;
                } else {
                    chip.classList.remove('all-checked');
                    stageBox.classList.remove('completed-stage');
                }
            }
        });

        const pct = total > 0 ? Math.round((checkedCount / total) * 100) : 0;
        
        const fill = card.querySelector(`#checklistFill-${scope}`);
        if (fill) fill.style.width = `${pct}%`;

        const percentLabel = card.querySelector(`#percentLabel-${scope}`);
        if (percentLabel) percentLabel.textContent = `${pct}%`;

        const itemCounter = card.querySelector(`#itemCounter-${scope}`);
        if (itemCounter) itemCounter.textContent = `${checkedCount} / ${total} Checked`;

        const stageCounter = card.querySelector(`#stageCounter-${scope}`);
        if (stageCounter) stageCounter.textContent = `${completedStagesCount} of ${totalStages} Stages Complete`;
    },

    async _toggleSolved(btn) {
        const pIdx = parseInt(btn.dataset.problemIdx, 10);
        if (isNaN(pIdx)) return;

        const currentData = this._lectureDataCache[this._selectedLectureId];
        const match = currentData?.matches?.[pIdx];
        const probId = match?.problem_id || `${this._selectedLectureId}-p${pIdx}`;

        const isCurrentlySolved = this._solvedIds.has(probId);
        if (isCurrentlySolved) {
            this._solvedIds.delete(probId);
            btn.classList.remove('active');
            btn.style.color = '';
            btn.style.borderColor = '';
            btn.style.background = '';
            btn.innerHTML = `${Icons.svg('circle', {class: 'icon-sm'})} Mark Solved`;
            App.showToast('Marked as unsolved', 'info');
        } else {
            this._solvedIds.add(probId);
            btn.classList.add('active');
            btn.style.color = 'var(--color-accent-green)';
            btn.style.borderColor = 'rgba(17,255,153,0.4)';
            btn.style.background = 'rgba(17,255,153,0.08)';
            btn.innerHTML = `${Icons.svg('check-circle', {class: 'icon-sm'})} Solved`;
            App.showToast('Marked as solved! 🎉', 'success');

            // Log attempt to backend if available
            try {
                await API.attempts.log({
                    problem_id: probId,
                    solved: 1,
                    used_hint: 0,
                    difficulty_felt: 3,
                    time_min: 15,
                    notes: 'Marked solved from Identified Problems explorer'
                });
            } catch (err) {
                console.error('Failed to log attempt to backend', err);
            }
        }
    },

    _updateHeader() {
        const currentLecture = this._lectures.find(l => l.id === this._selectedLectureId);
        const parsed = Utils.parseLectureTitle(currentLecture?.title, currentLecture?.num, currentLecture?.filename, currentLecture?.id);
        
        let subtitle = 'Review extracted algorithmic problems, verbal explanations, reconstructed Java solutions, and matched LeetCode challenges.';
        if (this._viewMode === 'question_detail') {
            const pIdx = (this._selectedProblemIndex || 0) + 1;
            const total = currentLecture?._problemCount || 1;
            subtitle = `${parsed.fullTitle} · Question ${pIdx} of ${total}`;
        }
        
        const subEl = document.querySelector('.page-header .page-subtitle');
        if (subEl) {
            subEl.textContent = subtitle;
        }
    }
};

window.ProblemsPage = ProblemsPage;
