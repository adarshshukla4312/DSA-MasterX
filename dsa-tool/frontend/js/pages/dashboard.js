const DashboardPage = {
    async render(container) {
        this.container = container;
        
        const todayStr = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
        
        container.innerHTML = `
            <div class="dashboard-page">
                ${Components.heroBanner('Revision Dashboard', `Track your SuperMemo SM-2 review schedules, retention velocity, and algorithmic pattern mastery across all DSA course modules. Today is ${todayStr}.`, 'Spaced Repetition Analytics')}
                
                <div class="grid-5 gap-md stagger-in" id="dashboardOverallStats" style="margin-bottom: 2rem;">
                    ${Components.skeletonCard()}
                    ${Components.skeletonCard()}
                    ${Components.skeletonCard()}
                    ${Components.skeletonCard()}
                    ${Components.skeletonCard()}
                </div>
                
                <hr style="margin: 2rem 0; border: none; border-top: 1px solid var(--color-hairline);" />
                
                ${Components.sectionHeader('Revision Due Today', '', 'repeat')}
                <div id="revisionDueContainer" style="margin-bottom: 2rem;">
                    ${Components.skeletonCard()}
                </div>
                
                <hr style="margin: 2rem 0; border: none; border-top: 1px solid var(--color-hairline);" />
                
                ${Components.sectionHeader('Revision Stats', '', 'trending-up')}
                <div class="grid-3 gap-md" id="revisionStatsContainer" style="margin-bottom: 2rem;">
                    ${Components.skeletonCard()}
                    ${Components.skeletonCard()}
                    ${Components.skeletonCard()}
                </div>
                
                <hr style="margin: 2rem 0; border: none; border-top: 1px solid var(--color-hairline);" />
                
                ${Components.sectionHeader('Recent Activity', '', 'bar-chart-2')}
                <div id="recentActivityContainer" class="flex-col gap-sm" style="margin-bottom: 2rem;">
                    ${Components.skeleton('100%', '48px')}
                    ${Components.skeleton('100%', '48px')}
                    ${Components.skeleton('100%', '48px')}
                </div>
                
                <hr style="margin: 2rem 0; border: none; border-top: 1px solid var(--color-hairline);" />
                
                ${Components.sectionHeader('Pattern Coverage', '', 'map')}
                <div class="glass-card" style="padding: 0; overflow-x: auto;">
                    <table class="coverage-table">
                        <thead>
                            <tr>
                                <th>Pattern</th>
                                <th style="text-align: center;">Solved</th>
                                <th style="text-align: center;">Total</th>
                                <th>Coverage</th>
                            </tr>
                        </thead>
                        <tbody id="patternCoverageTable">
                            <tr><td colspan="4" style="padding: 12px;">${Components.skeleton('100%', '32px')}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        this.attachEventListeners();
        await this.loadData();
    },

    async loadData() {
        try {
            const [
                stats,
                dueReviews,
                revStats,
                attempts,
                problems,
                solvedIds
            ] = await Promise.all([
                API.stats().catch(() => ({})),
                API.revision.due().catch(() => []),
                API.revision.stats().catch(() => ({})),
                API.attempts.list().catch(() => []),
                API.problems.list().catch(() => []),
                API.problems.solved().catch(() => ({ solved_ids: [] }))
            ]);

            this.problemsMap = new Map();
            if (problems && Array.isArray(problems)) {
                problems.forEach(p => this.problemsMap.set(p.id, p));
            }

            this.renderOverallStats(stats);
            this.renderRevisionDue(dueReviews);
            this.renderRevisionStats(revStats);
            this.renderRecentActivity(attempts);
            this.renderPatternCoverage(problems, solvedIds);
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
            App.showToast("Failed to load dashboard data", "error");
        }
    },

    renderOverallStats(stats) {
        const container = this.container.querySelector('#dashboardOverallStats');
        if (!container) return;

        const totalLectures = stats.total_lectures || 0;
        const processed = stats.processed_count ?? stats.processed_lectures ?? 0;
        const totalProblems = stats.total_problems || 0;
        const solved = stats.solved_count ?? stats.total_solved ?? 0;
        const totalAttempts = stats.total_attempts || 0;
        const accuracy = Math.round(stats.accuracy ?? stats.solve_rate ?? 0);

        container.innerHTML = `
            ${Components.statCard(`${processed}/${totalLectures}`, 'Processed', '#/library')}
            ${Components.statCard(totalProblems, 'Problem Database', '#/problems')}
            ${Components.statCard(solved, 'Solved', '#/practice')}
            ${Components.statCard(totalAttempts, 'Attempts', '#/dashboard')}
            ${Components.statCard(`${accuracy}%`, 'Accuracy', '#/dashboard')}
        `;
    },

    renderRevisionDue(dueReviews) {
        const container = this.container.querySelector('#revisionDueContainer');
        if (!container) return;

        if (!dueReviews || dueReviews.length === 0) {
            container.innerHTML = Components.emptyState(
                Icons.svg('party-popper', {style: 'width: 48px; height: 48px;'}),
                'All caught up! No patterns due for review today.',
                'Practice Sheets',
                '#/practice'
            );
            return;
        }

        const listHtml = `<div class="grid-2 gap-md stagger-in">${dueReviews.map(review => Components.reviewCard(review)).join('')}</div>`;
        container.innerHTML = listHtml;
    },

    renderRevisionStats(revStats) {
        const container = this.container.querySelector('#revisionStatsContainer');
        if (!container) return;

        container.innerHTML = `
            ${Components.statCard(revStats.total_patterns || 0, 'Tracked Patterns')}
            ${Components.statCard(revStats.due_today || 0, 'Due Today')}
            ${Components.statCard(revStats.mastered || 0, 'Mastered (>21d)')}
        `;
    },

    renderRecentActivity(attempts) {
        const container = this.container.querySelector('#recentActivityContainer');
        if (!container) return;

        if (!attempts || attempts.length === 0) {
            container.innerHTML = Components.emptyState(
                Icons.svg('trending-up', {style: 'width: 48px; height: 48px;'}),
                'No attempts logged yet. Start practicing!',
                'Practice Sheets',
                '#/practice'
            );
            return;
        }

        const recent = [...attempts].sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 10);
        
        container.innerHTML = recent.map(attempt => {
            const problem = this.problemsMap.get(attempt.problem_id);
            const title = problem ? problem.title : attempt.problem_id;
            return Components.activityItem(attempt, title);
        }).join('');
    },

    renderPatternCoverage(problems, solvedIds) {
        const container = this.container.querySelector('#patternCoverageTable');
        if (!container) return;

        if (!problems || problems.length === 0) {
            container.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;" class="caption">No problems found.</td></tr>';
            return;
        }

        const rawSolved = (solvedIds && solvedIds.solved_ids) 
            ? solvedIds.solved_ids 
            : (Array.isArray(solvedIds) ? solvedIds : []);
        const solvedSet = new Set(rawSolved);

        problems.forEach(p => {
            let patterns = p.patterns || [];
            if (typeof patterns === 'string') {
                try {
                    patterns = JSON.parse(patterns);
                } catch (e) {
                    patterns = [];
                }
            }
            if (!Array.isArray(patterns)) patterns = [];

            patterns.forEach(pat => {
                patternCounts.set(pat, (patternCounts.get(pat) || 0) + 1);
                if (solvedSet.has(p.id)) {
                    patternSolved.set(pat, (patternSolved.get(pat) || 0) + 1);
                }
            });
        });

        const rows = Array.from(patternCounts.entries()).map(([pat, count]) => {
            const solved = patternSolved.get(pat) || 0;
            const pct = count > 0 ? (solved / count) * 100 : 0;
            return { pat, solved, count, pct };
        });

        rows.sort((a, b) => {
            if (a.pct !== b.pct) return a.pct - b.pct;
            return b.count - a.count;
        });

        if (rows.length === 0) {
            container.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;" class="caption">No patterns found.</td></tr>';
            return;
        }

        container.innerHTML = rows.map(r => Components.coverageRow(r.pat, r.solved, r.count)).join('');
    },

    attachEventListeners() {
        this.handleAction = async (e) => {
            const btn = e.target.closest('button[data-action]');
            if (!btn) return;
            
            const action = btn.dataset.action;
            if (action === 'log-revision') {
                const pattern = btn.dataset.pattern;
                const problemId = btn.dataset.problemId;
                if (!problemId) {
                    App.showToast("No recommended problem for this pattern", "info");
                    return;
                }
                
                const problem = this.problemsMap ? this.problemsMap.get(problemId) : null;
                const title = problem ? problem.title : problemId;
                
                this.showAttemptModal(title, problemId, pattern);
            }
        };
        this.container.addEventListener('click', this.handleAction);
    },

    showAttemptModal(title, problemId) {
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
                
                const attemptData = {
                    problem_id: problemId,
                    solved: overlay.querySelector('#attemptSolved').checked ? 1 : 0,
                    used_hint: overlay.querySelector('#attemptHint').checked ? 1 : 0,
                    difficulty_felt: parseInt(diffSlider.value, 10),
                    time_min: parseInt(overlay.querySelector('#attemptTime').value, 10) || 0,
                    notes: overlay.querySelector('#attemptNotes').value || '',
                    date: new Date().toISOString()
                };
                
                try {
                    await API.attempts.log(attemptData);
                    App.showToast('Attempt logged successfully', 'success');
                    App.closeModal();
                    await this.loadData();
                } catch (err) {
                    console.error("Failed to log attempt:", err);
                    App.showToast(err.message || 'Failed to log attempt', 'error');
                    Utils.setButtonLoading(submitBtn, false);
                }
            });
        }
    },

    destroy() {
        if (this.container && this.handleAction) {
            this.container.removeEventListener('click', this.handleAction);
        }
        this.container = null;
        this.problemsMap = null;
    }
};

window.DashboardPage = DashboardPage;
