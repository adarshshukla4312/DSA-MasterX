const PracticePage = {
    _container: null,
    _lectures: [],
    _selectedLectureId: null,
    _activeTab: 0,
    _solvedIds: new Set(),
    _lectureDetails: null,
    _lectureMatches: null,
    _challengeData: null,
    _boundEvents: false,

    async render(container) {
        this._container = container;
        container.innerHTML = `
            ${Components.heroBanner('Practice Sheets', 'Master DSA concepts through interactive spaced-repetition quizzes, step-by-step problem ladders, and synthesis challenges.', 'Active Recall & Practice')}
            <div class="practice-hero-container">
                <div id="practiceLoader">${Components.skeleton('100%', '300px')}</div>
                <div id="practiceMain" style="display: none;">
                    <div id="lectureSelectorContainer" style="margin-bottom: 1.5rem;"></div>
                    <div class="practice-tabs-container">
                        ${Components.tabBar(['Warm-up Flashcards', 'MCQ Quiz', 'Concept Ladder', 'Questions for Practice', 'AI Challenge'], this._activeTab, 'practiceTabs')}
                    </div>
                    <div id="tabContent" style="margin-top: 1.5rem;"></div>
                </div>
            </div>
        `;
        
        if (!this._boundEvents) {
            this._bindEvents();
            this._boundEvents = true;
        }
        this._bindTabEvents();

        try {
            const [lecturesRes, solvedRes] = await Promise.all([
                API.lectures.list(),
                API.problems.solved()
            ]);
            
            this._lectures = (lecturesRes || []).filter(l => ['matched', 'extracted', 'identified', 'completed'].includes(l.status)).sort(Utils.compareLectures);
            
            if (solvedRes && solvedRes.solved_ids) {
                this._solvedIds = new Set(solvedRes.solved_ids);
            } else if (Array.isArray(solvedRes)) {
                this._solvedIds = new Set(solvedRes);
            }

            if (this._lectures.length === 0) {
                container.innerHTML = `
                    ${Components.pageHeader('Practice Sheets', 'Test conceptual understanding, build pattern mastery step-by-step, and practice real LeetCode problems.', 'red', 'Interactive Assignments & MCQs', 'file-check-2')}
                    <div class="practice-hero-container">
                        ${Components.emptyState(Icons.svg('file-check-2', {class: 'icon-xl', style: 'width: 32px; height: 32px;'}), 'No practice sheets yet! Process lectures in Lecture Library.')}
                    </div>
                `;
                return;
            }

            if (!this._selectedLectureId || !this._lectures.find(l => l.id === this._selectedLectureId)) {
                const populated = this._lectures.find(l => (l.mcqs && l.mcqs.length > 0) || (l.concept_ladder && l.concept_ladder.length > 0));
                this._selectedLectureId = populated ? populated.id : this._lectures[0].id;
            }

            const loader = document.getElementById('practiceLoader');
            const main = document.getElementById('practiceMain');
            if (loader) loader.style.display = 'none';
            if (main) main.style.display = 'block';

            await this._loadSelectedLecture();

        } catch (e) {
            console.error('Failed to load practice data', e);
            const loader = document.getElementById('practiceLoader');
            if (loader) {
                loader.innerHTML = Components.emptyState(Icons.svg('x-circle', {style: 'width: 48px; height: 48px;'}), 'Error loading practice data: ' + e.message);
            }
        }
    },

    destroy() {
        this._container = null;
        if (this._boundEvents) {
            document.removeEventListener('click', this._handleDocumentClick);
            document.removeEventListener('keydown', this._handleDocumentKeyDown);
            this._boundEvents = false;
        }
    },

    async _loadSelectedLecture() {
        const selectorContainer = document.getElementById('lectureSelectorContainer');
        const tabContent = document.getElementById('tabContent');
        if (!selectorContainer || !tabContent) return;

        tabContent.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
            </div>
        `;
        
        this._challengeData = null;

        try {
            const [details, matches] = await Promise.all([
                API.lectures.get(this._selectedLectureId),
                API.lectures.matches(this._selectedLectureId)
            ]);

            this._lectureDetails = details;
            this._lectureMatches = matches;
            
            this._renderSelector();
            this._renderTabContent();

        } catch (e) {
            console.error('Failed to load lecture details', e);
            tabContent.innerHTML = Components.emptyState(Icons.svg('x-circle', {style: 'width: 48px; height: 48px;'}), 'Error loading lecture details: ' + e.message);
        }
    },

    _renderSelector() {
        const container = document.getElementById('lectureSelectorContainer');
        if (!container) return;

        const currentIdx = this._lectures.findIndex(l => l.id === this._selectedLectureId);
        const currentLecture = this._lectures[currentIdx] || this._lectures[0];
        const parsed = Utils.parseLectureTitle(currentLecture?.title, currentLecture?.num, currentLecture?.filename, currentLecture?.id);

        const flashcardCount = (this._lectureDetails?.flashcards || []).length || 5;
        const mcqCount = (this._lectureDetails?.mcqs || []).length;
        const ladderCount = (this._lectureDetails?.concept_ladder || []).length;
        const problemCount = (this._lectureMatches || []).length;
        const totalLectures = this._lectures.length;

        const prevDisabled = currentIdx <= 0;
        const nextDisabled = currentIdx >= totalLectures - 1;

        container.innerHTML = `
            <div class="practice-lecture-hub">
                <div class="practice-hub-left">
                    <div class="lecture-picker-trigger" id="lecturePickerTrigger" role="button" tabindex="0" title="Click to choose a different lecture">
                        ${parsed.numStr ? `<span class="lecture-num-pill">${parsed.numStr}</span>` : ''}
                        <div class="picker-text-col">
                            ${parsed.module ? `<span class="picker-module-label">${Utils.escapeHtml(parsed.module)}</span>` : ''}
                            <span class="picker-topic-name">${Utils.escapeHtml(parsed.topic)}</span>
                        </div>
                        ${Icons.svg('chevron-down', {class: 'icon-sm picker-chevron'})}
                    </div>
                </div>

                <div class="practice-hub-right">
                    <div class="hub-metrics-group">
                        <button type="button" class="btn-ghost btn-sm flex-row gap-sm" data-action="open-framework-modal" title="Open complete Problem-Solving Framework Guide" style="color: var(--color-accent-green); border-color: rgba(17,255,153,0.3); background: rgba(17,255,153,0.06);">
                            ${Icons.svg('clipboard-check', {class: 'icon-xs'})} Framework Checklist
                        </button>
                        <span class="status-pill" style="color: #60a5fa; border-color: rgba(96,165,250,0.3); background: rgba(96,165,250,0.06);" title="Pre-Practice Flashcards">${Icons.svg('brain', {class: 'icon-xs'})} ${flashcardCount} Flashcards</span>
                        ${mcqCount ? `<span class="status-pill extracted" title="MCQ Questions">${Icons.svg('help-circle', {class: 'icon-xs'})} ${mcqCount} MCQs</span>` : ''}
                        ${ladderCount ? `<span class="status-pill" style="color: var(--color-accent-yellow); border-color: rgba(255,197,61,0.3); background: rgba(255,197,61,0.05);" title="Concept Steps">${Icons.svg('layers', {class: 'icon-xs'})} ${ladderCount} Steps</span>` : ''}
                        ${problemCount ? `<span class="status-pill completed" title="Problems Discussed">${Icons.svg('code-2', {class: 'icon-xs'})} ${problemCount} Problems</span>` : ''}
                    </div>
                </div>
            </div>
        `;

        // Setup Picker Trigger
        const trigger = document.getElementById('lecturePickerTrigger');
        if (trigger) {
            trigger.addEventListener('click', () => this._openLecturePickerModal());
            trigger.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this._openLecturePickerModal();
                }
            });
        }
    },

    _openLecturePickerModal() {
        App.showModal(Components.lecturePickerModal(this._lectures, this._selectedLectureId));

        const overlay = document.getElementById('modalOverlay');
        if (!overlay) return;

        const searchInput = overlay.querySelector('#modalLectureSearch');
        const listContainer = overlay.querySelector('#pickerModalList');

        if (searchInput && listContainer) {
            searchInput.focus();
            searchInput.addEventListener('input', Utils.debounce((e) => {
                const q = (e.target.value || '').toLowerCase().trim();
                const items = listContainer.querySelectorAll('.picker-modal-item');
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(q) ? 'flex' : 'none';
                });
            }, 150));
        }

        if (listContainer) {
            listContainer.addEventListener('click', (e) => {
                const item = e.target.closest('.picker-modal-item');
                if (item) {
                    const id = item.dataset.lectureId;
                    if (id) {
                        this._selectedLectureId = id;
                        App.closeModal();
                        this._loadSelectedLecture();
                    }
                }
            });
        }
    },

    _bindTabEvents() {
        const tabBar = document.getElementById('practiceTabs');
        if (!tabBar) return;
        
        tabBar.addEventListener('click', (e) => {
            const tabBtn = e.target.closest('.tab-item');
            if (tabBtn) {
                const tabIndex = parseInt(tabBtn.dataset.tab, 10);
                this._activeTab = tabIndex;
                
                Array.from(tabBar.children).forEach(btn => {
                    btn.classList.remove('active');
                    btn.setAttribute('aria-selected', 'false');
                });
                tabBtn.classList.add('active');
                tabBtn.setAttribute('aria-selected', 'true');
                
                this._renderTabContent();
            }
        });
    },

    _bindEvents() {
        this._handleDocumentClick = this._handleDocumentClick.bind(this);
        this._handleDocumentKeyDown = this._handleDocumentKeyDown.bind(this);
        document.addEventListener('click', this._handleDocumentClick);
        document.addEventListener('keydown', this._handleDocumentKeyDown);
    },

    _selectMcqOption(mcqOption) {
        const container = mcqOption.closest('.mcq-card') || document.getElementById(mcqOption.dataset.qid);
        if (!container || container.dataset.checked === 'true') return;
        
        container.querySelectorAll('.mcq-option').forEach(opt => {
            opt.classList.remove('selected');
            opt.setAttribute('aria-checked', 'false');
        });
        mcqOption.classList.add('selected');
        mcqOption.setAttribute('aria-checked', 'true');

        // Immediately evaluate on option click for instant responsive feedback
        this._evaluateMcq(container, mcqOption);
    },

    _evaluateMcq(container, selectedOpt) {
        if (!container || !selectedOpt) return;
        if (container.dataset.checked === 'true') return;

        container.dataset.checked = 'true';

        const selectedIdx = parseInt(selectedOpt.dataset.index, 10);
        const answerIdx = parseInt(container.dataset.answer, 10);
        const isCorrect = selectedIdx === answerIdx;

        let explanation = '';
        const mcqs = this._lectureDetails?.mcqs || [];
        const qid = container.id || '';
        const match = qid.match(/-(\d+)$/);
        if (match) {
            const idx = parseInt(match[1], 10);
            if (mcqs[idx]) explanation = mcqs[idx].explanation || '';
        }

        container.querySelectorAll('.mcq-option').forEach(opt => {
            const optIdx = parseInt(opt.dataset.index, 10);
            if (optIdx === answerIdx) {
                opt.classList.add('correct');
            } else if (optIdx === selectedIdx) {
                opt.classList.add('incorrect');
            }
        });

        const checkBtn = container.querySelector('[data-action="check-mcq"], [data-action="retry-mcq"]');
        if (checkBtn) {
            if (isCorrect) {
                checkBtn.innerHTML = `${Icons.svg('check-circle', {class: 'icon-sm'})} Verified Correct`;
                checkBtn.disabled = true;
                checkBtn.className = 'btn-ghost btn-sm mcq-correct-btn';
            } else {
                checkBtn.innerHTML = `${Icons.svg('refresh-cw', {class: 'icon-sm'})} Try Again`;
                checkBtn.dataset.action = 'retry-mcq';
                checkBtn.className = 'btn-ghost btn-sm mcq-retry-btn';
                checkBtn.disabled = false;
            }
        }

        const feedbackDiv = container.querySelector('.mcq-feedback');
        if (feedbackDiv) {
            feedbackDiv.style.display = 'block';
            if (isCorrect) {
                feedbackDiv.className = 'mcq-feedback correct';
                feedbackDiv.innerHTML = `
                    <div class="flex-row gap-sm" style="align-items: flex-start;">
                        ${Icons.svg('check-circle', {class: 'icon-md', style: 'color: var(--color-accent-green); margin-top: 1px; flex-shrink: 0;'})}
                        <div style="flex: 1;">
                            <div style="font-weight: 700; font-size: 13.5px; color: var(--color-accent-green); margin-bottom: 4px;">Verified Correct</div>
                            <div class="body-sm" style="color: #cbd5e1; line-height: 1.55;">${Utils.escapeHtml(explanation || 'Great job! You answered correctly.')}</div>
                        </div>
                    </div>`;
            } else {
                feedbackDiv.className = 'mcq-feedback incorrect';
                feedbackDiv.innerHTML = `
                    <div class="flex-row gap-sm" style="align-items: flex-start;">
                        ${Icons.svg('x-circle', {class: 'icon-md', style: 'color: #f87171; margin-top: 1px; flex-shrink: 0;'})}
                        <div style="flex: 1;">
                            <div style="font-weight: 700; font-size: 13.5px; color: #f87171; margin-bottom: 4px;">Incorrect Answer</div>
                            <div class="body-sm" style="color: #cbd5e1; line-height: 1.55;">${Utils.escapeHtml(explanation || 'Review the highlighted correct option and the lecture concepts, then try again.')}</div>
                        </div>
                    </div>`;
            }
        }
    },

    _handleDocumentKeyDown(e) {
        // Ignore if user is typing in an input, textarea, or contenteditable
        const tag = document.activeElement?.tagName?.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || document.activeElement?.isContentEditable) {
            return;
        }

        // 1. Flashcard Tab Keybindings (Active Tab 0)
        if (this._activeTab === 0) {
            const container = document.getElementById(`flashcardDeckContainer-${this._selectedLectureId}`);
            if (container) {
                const currentIdx = parseInt(container.dataset.currentIndex || '0', 10);
                const total = parseInt(container.dataset.total || '0', 10);

                if (e.code === 'Space') {
                    e.preventDefault();
                    const activeCard = container.querySelector(`.flashcard-3d-card.active`);
                    if (activeCard) {
                        activeCard.classList.toggle('flipped');
                    }
                    return;
                }

                if (e.key === 'ArrowRight' || e.key === 'j' || e.key === 'J') {
                    e.preventDefault();
                    if (currentIdx < total - 1) {
                        this._setFlashcardActive(currentIdx + 1, this._selectedLectureId);
                    }
                    return;
                }

                if (e.key === 'ArrowLeft' || e.key === 'k' || e.key === 'K') {
                    e.preventDefault();
                    if (currentIdx > 0) {
                        this._setFlashcardActive(currentIdx - 1, this._selectedLectureId);
                    }
                    return;
                }

                if (e.key === 'm' || e.key === 'M' || e.key === '1') {
                    e.preventDefault();
                    this._rateFlashcard(currentIdx, 'mastered', this._selectedLectureId);
                    return;
                }

                if (e.key === 'r' || e.key === 'R' || e.key === '2') {
                    e.preventDefault();
                    this._rateFlashcard(currentIdx, 'review', this._selectedLectureId);
                    return;
                }
            }
        }

        // 2. MCQ Option Selection via Enter / Space
        if (e.key === ' ' || e.key === 'Enter') {
            const mcqOption = document.activeElement?.closest('.mcq-option');
            if (mcqOption) {
                e.preventDefault();
                this._selectMcqOption(mcqOption);
            }
        }
    },

    _handleDocumentClick(e) {
        // --- Flashcard Deck Interactions ---
        const flipCardTarget = e.target.closest('[data-action="flip-flashcard"]');
        if (flipCardTarget) {
            const card = flipCardTarget.closest('.flashcard-3d-card');
            if (card) {
                card.classList.toggle('flipped');
            }
            return;
        }

        const flipBtn = e.target.closest('[data-action="flip-current-flashcard"]');
        if (flipBtn) {
            const lectureId = flipBtn.dataset.lectureId || this._selectedLectureId;
            const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
            const activeCard = container?.querySelector('.flashcard-3d-card.active');
            if (activeCard) {
                activeCard.classList.toggle('flipped');
            }
            return;
        }

        const prevFcBtn = e.target.closest('[data-action="prev-flashcard"]');
        if (prevFcBtn) {
            const lectureId = prevFcBtn.dataset.lectureId || this._selectedLectureId;
            const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
            const currentIdx = parseInt(container?.dataset.currentIndex || '0', 10);
            this._setFlashcardActive(currentIdx - 1, lectureId);
            return;
        }

        const nextFcBtn = e.target.closest('[data-action="next-flashcard"]');
        if (nextFcBtn) {
            const lectureId = nextFcBtn.dataset.lectureId || this._selectedLectureId;
            const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
            const currentIdx = parseInt(container?.dataset.currentIndex || '0', 10);
            this._setFlashcardActive(currentIdx + 1, lectureId);
            return;
        }

        const jumpFcBtn = e.target.closest('[data-action="jump-flashcard"]');
        if (jumpFcBtn) {
            const idx = parseInt(jumpFcBtn.dataset.index, 10);
            const container = jumpFcBtn.closest('.flashcard-deck-container');
            const lectureId = container?.dataset.lectureId || this._selectedLectureId;
            this._setFlashcardActive(idx, lectureId);
            return;
        }

        const rateFcBtn = e.target.closest('[data-action="rate-flashcard"]');
        if (rateFcBtn) {
            const idx = parseInt(rateFcBtn.dataset.index, 10);
            const rating = rateFcBtn.dataset.rating;
            const container = rateFcBtn.closest('.flashcard-deck-container');
            const lectureId = container?.dataset.lectureId || this._selectedLectureId;
            this._rateFlashcard(idx, rating, lectureId);
            return;
        }

        const regenFcBtn = e.target.closest('[data-action="regenerate-flashcards"]');
        if (regenFcBtn) {
            const lectureId = regenFcBtn.dataset.lectureId || this._selectedLectureId;
            this._regenerateFlashcards(regenFcBtn, lectureId);
            return;
        }

        const shuffleFcBtn = e.target.closest('[data-action="shuffle-flashcards"]');
        if (shuffleFcBtn) {
            const lectureId = shuffleFcBtn.dataset.lectureId || this._selectedLectureId;
            if (this._lectureDetails && Array.isArray(this._lectureDetails.flashcards)) {
                // Shuffle array in-place
                for (let i = this._lectureDetails.flashcards.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [this._lectureDetails.flashcards[i], this._lectureDetails.flashcards[j]] = [this._lectureDetails.flashcards[j], this._lectureDetails.flashcards[i]];
                }
                App.showToast('Flashcard deck shuffled!', 'info');
                this._renderTabContent();
            }
            return;
        }

        const toggleFcViewBtn = e.target.closest('[data-action="toggle-flashcard-view"]');
        if (toggleFcViewBtn) {
            const lectureId = toggleFcViewBtn.dataset.lectureId || this._selectedLectureId;
            const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
            const stageWrapper = document.getElementById(`fcStageWrapper-${lectureId}`);
            const gridView = document.getElementById(`fcGridView-${lectureId}`);
            const label = toggleFcViewBtn.querySelector('.view-mode-label');

            if (stageWrapper && gridView) {
                const isGrid = gridView.style.display !== 'none';
                if (isGrid) {
                    gridView.style.display = 'none';
                    stageWrapper.style.display = 'block';
                    if (label) label.textContent = 'Grid View';
                } else {
                    gridView.style.display = 'block';
                    stageWrapper.style.display = 'none';
                    if (label) label.textContent = 'Focus Deck';
                }
            }
            return;
        }

        const toggleListCardBtn = e.target.closest('[data-action="toggle-list-card"]');
        if (toggleListCardBtn) {
            const targetId = toggleListCardBtn.dataset.target;
            const body = document.getElementById(targetId);
            if (body) {
                const isHidden = body.style.display === 'none';
                body.style.display = isHidden ? 'block' : 'none';
            }
            return;
        }

        // MCQ Option Selection (Instant Check on Click)
        const mcqOption = e.target.closest('.mcq-option');
        if (mcqOption) {
            this._selectMcqOption(mcqOption);
        }

        // MCQ Check Answer Button
        const checkBtn = e.target.closest('[data-action="check-mcq"]');
        if (checkBtn) {
            const container = checkBtn.closest('.mcq-card') || document.getElementById(checkBtn.dataset.qid);
            if (!container) return;
            
            const selectedOpt = container.querySelector('.mcq-option.selected');
            if (!selectedOpt) {
                App.showToast('Please click an option to answer', 'info');
                return;
            }
            
            this._evaluateMcq(container, selectedOpt);
        }

        // MCQ Retry
        const retryBtn = e.target.closest('[data-action="retry-mcq"]');
        if (retryBtn) {
            const container = retryBtn.closest('.mcq-card') || document.getElementById(retryBtn.dataset.qid);
            if (!container) return;

            delete container.dataset.checked;
            container.querySelectorAll('.mcq-option').forEach(opt => {
                opt.classList.remove('selected', 'correct', 'incorrect');
                opt.setAttribute('aria-checked', 'false');
            });

            const feedbackDiv = container.querySelector('.mcq-feedback');
            if (feedbackDiv) {
                feedbackDiv.style.display = 'none';
                feedbackDiv.className = 'mcq-feedback';
                feedbackDiv.innerHTML = '';
            }

            retryBtn.innerHTML = `${Icons.svg('check', {class: 'icon-sm'})} Check Answer`;
            retryBtn.dataset.action = 'check-mcq';
            retryBtn.className = 'btn-primary btn-sm';
            retryBtn.disabled = false;
        }

        // Log Attempt Button
        const logBtn = e.target.closest('[data-action="log-attempt"]');
        if (logBtn) {
            const problemId = logBtn.dataset.problem;
            let title = problemId;
            
            const ladderStep = (this._lectureDetails?.concept_ladder || []).find(s => s.id === problemId || s.title === problemId);
            if (ladderStep) title = ladderStep.title;
            else {
                const matchProb = (this._lectureMatches || []).find(m => m.problem_id === problemId);
                if (matchProb) title = matchProb.title;
            }
            
            this._showAttemptModal(title, problemId);
        }

        // Generate AI Challenge
        const genChallengeBtn = e.target.closest('[data-action="generate-challenge"]');
        if (genChallengeBtn) {
            this._generateChallenge(genChallengeBtn);
            return;
        }

        // Open Global Framework Modal
        const frameworkModalBtn = e.target.closest('[data-action="open-framework-modal"]');
        if (frameworkModalBtn) {
            App.showModal(Components.methodologyModal(this._selectedLectureId, this._lectureDetails?.title || 'Problem Solving Framework'));
            this._restoreAllChecklists();
            return;
        }

        // Toggle Problem Specific Checklist Drawer
        const toggleProbChkBtn = e.target.closest('[data-action="toggle-problem-checklist"]');
        if (toggleProbChkBtn) {
            const probId = toggleProbChkBtn.dataset.problemId;
            const drawer = document.getElementById(`problemChecklistDrawer-${probId}`);
            if (drawer) {
                const isHidden = drawer.style.display === 'none';
                drawer.style.display = isHidden ? 'block' : 'none';
                toggleProbChkBtn.classList.toggle('active', isHidden);
                if (isHidden) {
                    this._restoreChecklist(probId);
                    if (typeof anime !== 'undefined') {
                        anime({
                            targets: drawer,
                            opacity: [0, 1],
                            translateY: [-6, 0],
                            duration: 200,
                            easing: 'easeOutCubic'
                        });
                    }
                }
            }
            return;
        }

        // Toggle Stage Accordion
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

        // Toggle All Stages
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

        // Reset Checklist
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

        // Toggle Interview Verbal Mode
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

        // Methodology Checkbox Click
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
    },

    async _generateChallenge(btn) {
        if (!this._selectedLectureId) return;
        Utils.setButtonLoading(btn, true);
        
        try {
            const challenge = await API.lectures.challenge(this._selectedLectureId);
            this._challengeData = challenge;
            App.showToast('Bespoke AI Challenge generated!', 'success');
            this._renderTabContent();
        } catch (e) {
            App.showToast('Failed to generate challenge: ' + e.message, 'error');
            Utils.setButtonLoading(btn, false);
        }
    },

    _showAttemptModal(title, problemId) {
        const modalHtml = Components.attemptModal(title, problemId);
        App.showModal(modalHtml);
        
        const overlay = document.getElementById('modalOverlay');
        if (!overlay) return;
        
        const form = overlay.querySelector('#attemptForm');
        const diffSlider = overlay.querySelector('#attemptDifficulty');
        const diffDisplay = overlay.querySelector('#difficultyDisplay');
        
        if (diffSlider && diffDisplay) {
            const updateSliderDisplay = (val) => {
                diffDisplay.textContent = `Level ${val}`;
                if (val <= 2) diffDisplay.style.color = 'var(--color-accent-green)';
                else if (val === 3) diffDisplay.style.color = 'var(--color-accent-yellow)';
                else diffDisplay.style.color = 'var(--color-accent-red)';
            };
            updateSliderDisplay(diffSlider.value);
            diffSlider.addEventListener('input', (e) => updateSliderDisplay(e.target.value));
        }
        
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const submitBtn = form.querySelector('button[type="submit"]');
                Utils.setButtonLoading(submitBtn, true);
                
                const data = {
                    problem_id: problemId,
                    solved: overlay.querySelector('#attemptSolved').checked ? 1 : 0,
                    used_hint: overlay.querySelector('#attemptHint').checked ? 1 : 0,
                    difficulty_felt: parseInt(diffSlider.value, 10),
                    time_min: parseInt(overlay.querySelector('#attemptTime').value, 10) || 0,
                    notes: overlay.querySelector('#attemptNotes').value || ''
                };
                
                try {
                    await API.attempts.log(data);
                    App.showToast('Attempt logged successfully!', 'success');
                    
                    if (data.solved) {
                        this._solvedIds.add(problemId);
                    }
                    
                    App.closeModal();
                    this._renderTabContent();
                    
                } catch (err) {
                    App.showToast('Failed to log attempt: ' + err.message, 'error');
                    Utils.setButtonLoading(submitBtn, false);
                }
            });
        }
    },

    _renderTabContent() {
        const contentArea = document.getElementById('tabContent');
        if (!contentArea) return;

        let html = '';
        switch (this._activeTab) {
            case 0:
                html = this._renderFlashcardsTab();
                break;
            case 1:
                html = this._renderMCQTab();
                break;
            case 2:
                html = this._renderLadderTab();
                break;
            case 3:
                html = this._renderProblemsTab();
                break;
            case 4:
                html = this._renderChallengeTab();
                break;
        }

        contentArea.innerHTML = html;
        contentArea.className = 'stagger-in';

        // If flashcard tab, restore deck state and active card
        if (this._activeTab === 0) {
            this._restoreFlashcardsDeck(this._selectedLectureId);
        }

        // Restore saved checklist states & calculate progress
        this._restoreAllChecklists();

        // Animate child cards with Anime.js if available
        if (typeof anime !== 'undefined') {
            anime({
                targets: contentArea.querySelectorAll('.mcq-card, .ladder-step, .glass-card, .methodology-checklist-card, .flashcard-deck-container'),
                opacity: [0, 1],
                translateY: [14, 0],
                delay: anime.stagger(40),
                duration: 300,
                easing: 'easeOutQuad'
            });
        }
    },

    _renderFlashcardsTab() {
        const flashcards = this._lectureDetails?.flashcards || [];
        if (!flashcards.length) {
            return Components.emptyState(Icons.svg('brain', {style: 'width: 48px; height: 48px;'}), 'No flashcards available for this lecture yet. Click AI Refresh above to generate them!');
        }

        return Components.flashcardDeck(flashcards, this._selectedLectureId);
    },

    _restoreFlashcardsDeck(lectureId) {
        if (!lectureId) return;
        const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
        if (!container) return;

        let mastery = {};
        try {
            const saved = localStorage.getItem(`dsa_fc_mastery_${lectureId}`);
            if (saved) mastery = JSON.parse(saved);
        } catch (e) {}

        const total = parseInt(container.dataset.total, 10) || 0;
        let masteredCount = 0;

        container.querySelectorAll('.flashcard-3d-card').forEach((card, idx) => {
            const rating = mastery[idx];
            const dot = container.querySelector(`.flashcard-dot-btn[data-index="${idx}"]`);
            const reviewBtn = card.querySelector(`.rating-review[data-index="${idx}"]`);
            const masteredBtn = card.querySelector(`.rating-mastered[data-index="${idx}"]`);

            if (rating === 'mastered') {
                masteredCount++;
                if (dot) dot.classList.add('mastered');
                if (masteredBtn) masteredBtn.classList.add('active');
            } else if (rating === 'review') {
                if (dot) dot.classList.add('review');
                if (reviewBtn) reviewBtn.classList.add('active');
            }
        });

        const countLabel = container.querySelector(`#fcMasteryCount-${lectureId}`);
        if (countLabel) countLabel.textContent = `${masteredCount} / ${total} Mastered`;

        this._setFlashcardActive(0, lectureId);
    },

    _setFlashcardActive(index, lectureId) {
        if (!lectureId) return;
        const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
        if (!container) return;

        const total = parseInt(container.dataset.total, 10) || 0;
        if (index < 0) index = 0;
        if (index >= total) index = total - 1;

        container.dataset.currentIndex = index;

        // Cards visibility
        container.querySelectorAll('.flashcard-3d-card').forEach((c, idx) => {
            if (idx === index) {
                c.classList.add('active');
            } else {
                c.classList.remove('active', 'flipped');
            }
        });

        // Dots
        container.querySelectorAll('.flashcard-dot-btn').forEach((dot, idx) => {
            dot.classList.toggle('active', idx === index);
        });

        // Counter
        const counter = container.querySelector(`#fcCurrentNum-${lectureId}`);
        if (counter) counter.textContent = `Card ${index + 1} of ${total}`;

        // Prev/Next buttons
        const prevBtn = container.querySelector(`#fcPrevBtn-${lectureId}`);
        const nextBtn = container.querySelector(`#fcNextBtn-${lectureId}`);
        if (prevBtn) prevBtn.disabled = index === 0;
        if (nextBtn) nextBtn.disabled = index === total - 1;
    },

    _rateFlashcard(index, rating, lectureId) {
        if (!lectureId) return;
        const container = document.getElementById(`flashcardDeckContainer-${lectureId}`);
        if (!container) return;

        let mastery = {};
        try {
            const saved = localStorage.getItem(`dsa_fc_mastery_${lectureId}`);
            if (saved) mastery = JSON.parse(saved);
        } catch (e) {}

        mastery[index] = rating;
        localStorage.setItem(`dsa_fc_mastery_${lectureId}`, JSON.stringify(mastery));

        const card = container.querySelector(`#fcCard-${lectureId}-${index}`);
        if (card) {
            const reviewBtn = card.querySelector(`.rating-review[data-index="${index}"]`);
            const masteredBtn = card.querySelector(`.rating-mastered[data-index="${index}"]`);
            if (reviewBtn) reviewBtn.classList.toggle('active', rating === 'review');
            if (masteredBtn) masteredBtn.classList.toggle('active', rating === 'mastered');
        }

        const dot = container.querySelector(`.flashcard-dot-btn[data-index="${index}"]`);
        if (dot) {
            dot.classList.toggle('mastered', rating === 'mastered');
            dot.classList.toggle('review', rating === 'review');
        }

        // Update counter
        const total = parseInt(container.dataset.total, 10) || 0;
        const masteredCount = Object.values(mastery).filter(v => v === 'mastered').length;
        const countLabel = container.querySelector(`#fcMasteryCount-${lectureId}`);
        if (countLabel) countLabel.textContent = `${masteredCount} / ${total} Mastered`;

        // Automatically advance to next card if not on last card
        const currentIdx = parseInt(container.dataset.currentIndex || '0', 10);
        if (currentIdx < total - 1) {
            setTimeout(() => {
                this._setFlashcardActive(currentIdx + 1, lectureId);
            }, 250);
        }
    },

    async _regenerateFlashcards(btn, lectureId) {
        if (!lectureId) return;
        Utils.setButtonLoading(btn, true);

        try {
            const res = await API.lectures.generateFlashcards(lectureId);
            if (res && res.flashcards) {
                if (this._lectureDetails) {
                    this._lectureDetails.flashcards = res.flashcards;
                }
                localStorage.removeItem(`dsa_fc_mastery_${lectureId}`);
                App.showToast('Generated 5 fresh interview recall flashcards!', 'success');
                this._renderTabContent();
            }
        } catch (e) {
            App.showToast('Failed to generate flashcards: ' + e.message, 'error');
            Utils.setButtonLoading(btn, false);
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

    _renderMCQTab() {
        const mcqs = this._lectureDetails?.mcqs || [];
        if (!mcqs.length) {
            return Components.emptyState(Icons.svg('file-text', {style: 'width: 48px; height: 48px;'}), 'No MCQs available for this lecture yet.');
        }

        const level1 = mcqs.filter(q => q.level === 1);
        const level2 = mcqs.filter(q => q.level === 2);
        
        if (!level1.length && !level2.length) {
            const mid = Math.max(1, Math.floor(mcqs.length / 2));
            level1.push(...mcqs.slice(0, mid));
            level2.push(...mcqs.slice(mid));
        }

        let html = `
        <div class="mcq-section">
            <div class="mcq-score-banner">
                <div class="flex-row gap-sm" style="align-items: center;">
                    ${Icons.svg('help-circle', {class: 'icon-sm', style: 'color: var(--color-accent-blue);'})}
                    <span><strong>${mcqs.length} Questions</strong> across 2 Mastery Levels</span>
                </div>
                <div class="caption">Click any option to test your understanding</div>
            </div>
        `;
        
        if (level1.length) {
            html += `
                <div style="margin-bottom: 2.5rem;">
                    <div class="mcq-level-header">
                        <div class="flex-row gap-sm" style="align-items: center; margin-bottom: 4px;">
                            <span class="lecture-num-pill" style="color: var(--color-accent-blue); border-color: rgba(59,158,255,0.4); background: rgba(59,158,255,0.1);">Level 1</span>
                            <h3 class="heading-md">Knowledge Retrieval</h3>
                        </div>
                        <p class="caption">Direct recall test. If you watched the entire video, you should be able to answer all of these questions.</p>
                    </div>
                    <div class="flex-col gap-md">
                        ${level1.map(q => {
                            const originalIndex = mcqs.indexOf(q);
                            return Components.mcqCard(q, originalIndex, this._selectedLectureId);
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        if (level2.length) {
            html += `
                <div>
                    <div class="mcq-level-header">
                        <div class="flex-row gap-sm" style="align-items: center; margin-bottom: 4px;">
                            <span class="lecture-num-pill" style="color: var(--color-accent-yellow); border-color: rgba(255,197,61,0.4); background: rgba(255,197,61,0.1);">Level 2</span>
                            <h3 class="heading-md">Critical Reflection & Reasoning</h3>
                        </div>
                        <p class="caption">Critical questions to challenge your understanding and make you reflect deeply on edge cases.</p>
                    </div>
                    <div class="flex-col gap-md">
                        ${level2.map(q => {
                            const originalIndex = mcqs.indexOf(q);
                            return Components.mcqCard(q, originalIndex, this._selectedLectureId);
                        }).join('')}
                    </div>
                </div>
            `;
        }

        html += `</div>`;
        return html;
    },

    _renderLadderTab() {
        const ladder = this._lectureDetails?.concept_ladder || [];
        if (!ladder.length) {
            return Components.emptyState(Icons.svg('layers', {style: 'width: 48px; height: 48px;'}), 'No Concept Ladder available for this lecture yet.');
        }

        return `
            <div class="mcq-section">
                <div style="margin-bottom: 2rem; text-align: center;">
                    <h3 class="heading-lg" style="margin-bottom: 6px;">Progressive Concept Ladder</h3>
                    <p class="caption">A systematically ordered sequence of real LeetCode problems building from warm-up to synthesis.</p>
                </div>
                <div class="concept-ladder flex-col gap-md">
                    ${ladder.map((step, idx) => {
                        const probId = step.id || step.title;
                        const isSolved = this._solvedIds.has(probId);
                        const diff = step.difficulty || 'Medium';
                        const searchUrl = Utils.googleSearchUrl(step.title, step.platform || 'LeetCode');
                        const why = step.why_this_problem || '';

                        return `
                        <div class="ladder-step ${isSolved ? 'completed' : ''}">
                            <div class="step-node ${isSolved ? 'completed' : ''}">
                                ${isSolved ? Icons.svg('check', {class: 'icon-xs'}) : `<span class="step-number">${idx + 1}</span>`}
                            </div>
                            <div class="step-content glass-card">
                                <div class="flex-between">
                                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                        ${isSolved ? Icons.svg('check-circle-2', {class: 'icon-md diff-easy'}) : Icons.svg('circle', {class: 'icon-md caption'})}
                                        <span class="body-md"><strong>${Utils.escapeHtml(step.title)}</strong></span>
                                        ${Components.difficultyBadge(diff)}
                                    </div>
                                    <div class="flex-row gap-xs">
                                        <button class="btn-ghost btn-sm flex-row gap-sm" data-action="toggle-problem-checklist" data-problem-id="${Utils.escapeHtml(probId)}" title="Open Problem Solving Methodology Checklist">
                                            ${Icons.svg('clipboard-check', {class: 'icon-xs'})} Checklist
                                        </button>
                                        <button class="btn-ghost btn-sm flex-row gap-sm" data-action="log-attempt" data-problem="${Utils.escapeHtml(probId)}">
                                            ${Icons.svg('bar-chart-2', {class: 'icon-sm'})} Log
                                        </button>
                                    </div>
                                </div>
                                <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" class="body-sm flex-row gap-sm problem-search-link" style="margin-top: 8px; display: inline-flex;">
                                    ${Icons.svg('search', {class: 'icon-sm'})} Search on ${Utils.escapeHtml(step.platform || 'LeetCode')}
                                </a>
                                ${why ? `<div class="caption flex-row gap-sm" style="margin-top: 6px; align-items: flex-start;">${Icons.svg('lightbulb', {class: 'icon-sm', style: 'flex-shrink: 0'})} <span>${Utils.escapeHtml(why)}</span></div>` : ''}

                                <div class="problem-checklist-drawer" id="problemChecklistDrawer-${Utils.escapeHtml(probId)}" style="display: none; margin-top: 14px;">
                                    ${Components.methodologyChecklist(probId, { embedded: true, defaultOpen: false, title: `Problem Solving Protocol · Step ${idx + 1}: ${step.title}` })}
                                </div>
                            </div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
        `;
    },

    _renderProblemsTab() {
        const problems = this._lectureMatches || [];
        const lectureScope = `lecture_${this._selectedLectureId}`;

        if (!problems.length) {
            return `
                <div class="mcq-section">
                    ${Components.methodologyChecklist(lectureScope, { title: 'Problem-Solving Methodology Framework', defaultOpen: false })}
                    ${Components.emptyState(Icons.svg('target', {style: 'width: 48px; height: 48px;'}), 'No confirmed practice problems yet for this lecture.')}
                </div>
            `;
        }

        return `
            <div class="mcq-section">
                <!-- Master Problem-Solving Methodology Checklist -->
                <div style="margin-bottom: 2rem;">
                    ${Components.methodologyChecklist(lectureScope, { title: 'Problem-Solving Methodology Framework', defaultOpen: false })}
                </div>

                <div style="margin-bottom: 1.5rem; text-align: center;">
                    <h3 class="heading-lg" style="margin-bottom: 6px;">Questions for Practice</h3>
                    <p class="caption">Direct algorithmic exercises extracted from the lecture session. Apply the systematic solving protocol below.</p>
                </div>

                <div class="flex-col gap-md">
                    ${problems.map(prob => {
                        const isSolved = this._solvedIds.has(prob.problem_id);
                        const diffBadge = Components.difficultyBadge(prob.difficulty || 'Medium');
                        const tags = Components.tagPills(Array.isArray(prob.patterns) ? prob.patterns : (typeof prob.patterns === 'string' ? JSON.parse(prob.patterns || '[]') : []));
                        const searchUrl = Utils.googleSearchUrl(prob.title, prob.platform || 'LeetCode');
                        
                        return `
                            <div class="glass-card">
                                <div class="flex-between" style="flex-wrap: wrap; gap: 8px;">
                                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                        ${isSolved ? Icons.svg('check-circle-2', {class: 'icon-md diff-easy'}) : Icons.svg('circle', {class: 'icon-md caption'})}
                                        <span class="body-md"><strong>${Utils.escapeHtml(prob.title)}</strong></span>
                                        ${diffBadge}
                                    </div>
                                    <div class="flex-row gap-xs">
                                        <button class="btn-ghost btn-sm flex-row gap-sm" data-action="toggle-problem-checklist" data-problem-id="${Utils.escapeHtml(prob.problem_id)}" title="Open Problem Solving Methodology Checklist">
                                            ${Icons.svg('clipboard-check', {class: 'icon-xs'})} Solving Checklist
                                        </button>
                                        <button class="btn-ghost btn-sm flex-row gap-sm" data-action="log-attempt" data-problem="${Utils.escapeHtml(prob.problem_id)}">
                                            ${Icons.svg('bar-chart-2', {class: 'icon-sm'})} Log Attempt
                                        </button>
                                    </div>
                                </div>
                                <div style="margin-top: 10px;">${tags}</div>
                                <div style="margin-top: 12px;">
                                    <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" class="body-sm flex-row gap-sm problem-search-link" style="display: inline-flex;">
                                        ${Icons.svg('search', {class: 'icon-sm'})} Search on ${Utils.escapeHtml(prob.platform || 'LeetCode')}
                                    </a>
                                </div>
                                ${prob.timestamp_start && prob.timestamp_end ? `
                                    <div class="caption flex-row gap-sm" style="margin-top: 8px;">${Icons.svg('clock', {class: 'icon-sm'})} Discussed: ${Utils.escapeHtml(prob.timestamp_start)} — ${Utils.escapeHtml(prob.timestamp_end)}</div>
                                ` : ''}

                                <!-- Problem Specific Checklist Drawer -->
                                <div class="problem-checklist-drawer" id="problemChecklistDrawer-${Utils.escapeHtml(prob.problem_id)}" style="display: none; margin-top: 14px;">
                                    ${Components.methodologyChecklist(prob.problem_id, { embedded: true, defaultOpen: false, title: `Solving Protocol · ${prob.title}` })}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    },

    _renderChallengeTab() {
        const challengeScope = `challenge_${this._selectedLectureId}`;
        if (!this._challengeData) {
            return `
                <div class="mcq-section" style="text-align: center; padding: 2rem 0;">
                    <div style="margin-bottom: 24px;">
                        <h3 class="heading-lg" style="margin-bottom: 8px;">Bespoke AI Assignment Challenge</h3>
                        <p class="caption">Synthesize a brand-new assignment challenge problem tailored to this lecture.</p>
                    </div>
                    <button class="btn-primary" data-action="generate-challenge">${Icons.svg('zap', {class: 'icon-sm'})} Generate Custom Challenge</button>
                </div>
            `;
        }

        const c = this._challengeData;
        const samples = c.sample_cases || [];

        let samplesHtml = '';
        if (samples.length) {
            samplesHtml = `
                <h4 class="heading-sm" style="margin-top: 16px;">Sample Test Cases</h4>
                ${samples.map((sc, idx) => `
                    <div style="margin-top: 8px;">
                        ${Components.codeBlock(`Sample Input ${idx + 1}:\n${sc.input}\n\nSample Output ${idx + 1}:\n${sc.output}`)}
                        ${sc.explanation ? `<div class="caption" style="margin-top: 4px;">Explanation: ${Utils.escapeHtml(sc.explanation)}</div>` : ''}
                    </div>
                `).join('')}
            `;
        }

        return `
            <div class="mcq-section">
                <div style="margin-bottom: 24px; text-align: center;">
                    <h3 class="heading-lg" style="margin-bottom: 8px;">Bespoke AI Assignment Challenge</h3>
                    <p class="caption">Synthesize a brand-new assignment challenge problem for this lecture.</p>
                </div>
                
                <div class="glass-card">
                    <div class="flex-between" style="flex-wrap: wrap; gap: 8px;">
                        <h4 class="heading-md flex-row gap-sm">${Utils.escapeHtml(c.title || 'Custom Challenge')} ${Components.difficultyBadge(c.difficulty || 'Medium')}</h4>
                        <button class="btn-ghost btn-sm flex-row gap-sm" data-action="toggle-problem-checklist" data-problem-id="${Utils.escapeHtml(challengeScope)}">
                            ${Icons.svg('clipboard-check', {class: 'icon-xs'})} Solving Protocol
                        </button>
                    </div>
                    <div class="body-sm" style="margin-top: 12px; margin-bottom: 12px;">
                        <strong>Target Complexity:</strong> <code style="color: var(--color-accent-blue);">${Utils.escapeHtml(c.target_complexity || 'O(N)')}</code>
                    </div>
                    
                    <h4 class="heading-sm">Problem Statement</h4>
                    <p class="body-md" style="white-space: pre-wrap; margin-bottom: 12px;">${Utils.escapeHtml(c.problem_statement || '')}</p>
                    
                    <div class="body-sm" style="margin-bottom: 4px;"><strong>Input Format:</strong> ${Utils.escapeHtml(c.input_format || '')}</div>
                    <div class="body-sm" style="margin-bottom: 4px;"><strong>Output Format:</strong> ${Utils.escapeHtml(c.output_format || '')}</div>
                    <div class="body-sm" style="margin-bottom: 16px;"><strong>Constraints:</strong> <code>${Utils.escapeHtml(c.constraints || '')}</code></div>
                    
                    ${samplesHtml}

                    <!-- Challenge Checklist Drawer -->
                    <div class="problem-checklist-drawer" id="problemChecklistDrawer-${Utils.escapeHtml(challengeScope)}" style="display: none; margin-top: 16px;">
                        ${Components.methodologyChecklist(challengeScope, { embedded: true, defaultOpen: true, title: `Solving Protocol · ${c.title || 'Custom Challenge'}` })}
                    </div>
                    
                    <div style="margin-top: 24px; border-top: 1px solid var(--color-hairline); padding-top: 16px;">
                        <details style="margin-bottom: 12px; cursor: pointer;">
                            <summary class="body-sm flex-row gap-sm" style="color: var(--color-accent-yellow); display: inline-flex;">${Icons.svg('lightbulb', {class: 'icon-sm'})} View Hint</summary>
                            <div class="glass-card" style="margin-top: 8px; border-color: var(--color-accent-yellow);">
                                ${Utils.escapeHtml(c.hint || 'No hint available.')}
                            </div>
                        </details>
                        
                        <details style="cursor: pointer;">
                            <summary class="body-sm flex-row gap-sm" style="color: var(--color-accent-green); display: inline-flex;">${Icons.svg('key', {class: 'icon-sm'})} View Solution Strategy</summary>
                            <div class="glass-card" style="margin-top: 8px; border-color: var(--color-accent-green);">
                                ${Utils.escapeHtml(c.solution_strategy || 'No strategy provided.')}
                            </div>
                        </details>
                    </div>
                </div>
                
                <div style="margin-top: 24px; text-align: center;">
                    <button class="btn-primary" data-action="generate-challenge">${Icons.svg('zap', {class: 'icon-sm'})} Generate Another Challenge</button>
                </div>
            </div>
        `;
    }
};

window.PracticePage = PracticePage;

