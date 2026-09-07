/**
 * DSA Mastery Engine — Reusable UI Components
 * 
 * Every function returns an HTML string.
 */

const Components = {

    // ── Glow Page Header ─────────────────────────────────────────────
    pageHeader(title, subtitle, glowColor = 'blue', pillText = '', icon = '') {
        const iconHtml = icon ? Icons.svg(icon, {class: 'icon-lg', style: 'margin-right: 10px; vertical-align: -2px;'}) : '';
        const titleStr = typeof title === 'string' ? title : '';
        const isHtml = titleStr.includes('<svg') || titleStr.includes('<i');
        const titleContent = isHtml ? titleStr : `${iconHtml}${Utils.escapeHtml(titleStr)}`;
        return `
        <div class="page-header">
            ${pillText ? `
            <div class="badge-pill" style="margin-bottom: 8px;">
                ${Icons.svg('sparkles', {class: 'icon-sm', style: 'color: var(--color-accent-blue);'})}
                <span>${Utils.escapeHtml(pillText)}</span>
            </div>` : ''}
            <h1 class="display-xl" style="display: flex; align-items: center;">${titleContent}</h1>
            ${subtitle ? `<p class="body-sm page-subtitle" style="margin-top: 6px; color: var(--color-ash);">${Utils.escapeHtml(subtitle)}</p>` : ''}
        </div>`;
    },

    // ── Hero Banner (Home page) ──────────────────────────────────────
    heroBanner(title, description, pillText = '') {
        return `
        <div class="hero-banner">
            ${pillText ? `
            <div class="badge-pill" style="margin-bottom: 16px;">
                ${Icons.svg('sparkles', {class: 'icon-sm', style: 'color: var(--color-accent-green);'})}
                <span>${Utils.escapeHtml(pillText)}</span>
            </div>` : ''}
            <h1 class="display-xxl" style="margin-bottom: 12px;">${Utils.escapeHtml(title)}</h1>
            <p class="body-lg" style="max-width: 820px; margin: 0; line-height: 1.6;">
                ${Utils.escapeHtml(description)}
            </p>
        </div>`;
    },

    // ── Stat Card (Clickable) ─────────────────────────────────────────
    statCard(value, label, href = '') {
        const tag = href ? 'a' : 'div';
        const hrefAttr = href ? ` href="${Utils.escapeHtml(href)}"` : '';
        return `
        <${tag} class="stat-card"${hrefAttr}>
            <div class="value">${Utils.escapeHtml(String(value))}</div>
            <div class="label">${Utils.escapeHtml(label)}</div>
        </${tag}>`;
    },

    // ── Glass Card ───────────────────────────────────────────────────
    glassCard(content, extraClass = '') {
        return `<div class="glass-card ${extraClass}">${content}</div>`;
    },

    // ── Status Pill ──────────────────────────────────────────────────
    _statusIcon(status) {
        const s = (status || 'new').toLowerCase();
        if (s === 'completed' || s === 'complete' || s === 'identified' || s === 'matched' || s === 'extracted') return 'check';
        if (s === 'transcribed') return 'file-text';
        if (s === 'processing' || s === 'starting') return 'refresh-cw';
        if (s === 'new') return 'clock';
        return 'clock';
    },

    statusPill(status) {
        const s = (status || 'new').toLowerCase();
        const label = Utils.statusLabel(status);
        const iconName = Components._statusIcon(status);
        let pillClass = s;
        if (s === 'completed' || s === 'complete' || s === 'identified' || s === 'matched' || s === 'extracted') {
            pillClass = 'completed';
        } else if (s === 'transcribed') {
            pillClass = 'incomplete';
        }
        return `<span class="status-pill ${pillClass}">
            ${Icons.svg(iconName, {class: 'icon-xs status-icon-badge'})}
            <span>${Utils.escapeHtml(label)}</span>
        </span>`;
    },

    _statusColor(status) {
        const map = {
            'new': 'orange',
            'transcribed': 'yellow',
            'extracted': 'blue',
            'identified': 'green',
            'matched': 'green',
            'completed': 'green',
            'outdated': 'orange',
        };
        return map[status] || 'orange';
    },

    // ── Badge Pill ───────────────────────────────────────────────────
    badgePill(text) {
        return `<span class="badge-pill">${Utils.escapeHtml(text)}</span>`;
    },

    // ── Tag Pills (for topics/patterns) ──────────────────────────────
    tagPills(tags) {
        if (!tags || !tags.length) return '';
        return `<div class="flex-row gap-sm" style="flex-wrap: wrap;">
            ${tags.map(t => `<span class="tag-pill">${Utils.escapeHtml(t)}</span>`).join('')}
        </div>`;
    },

    // ── Difficulty Badge ─────────────────────────────────────────────
    difficultyBadge(difficulty) {
        const d = (difficulty || 'Medium').toLowerCase();
        const label = d.charAt(0).toUpperCase() + d.slice(1);
        return `<span class="diff-${d}">[${Utils.escapeHtml(label)}]</span>`;
    },

    // ── Progress Bar ─────────────────────────────────────────────────
    progressBar(percent, label = '') {
        const clamped = Math.min(100, Math.max(0, percent));
        return `
        <div style="margin-bottom: 4px;">
            ${label ? `<div class="flex-between" style="margin-bottom: 4px;">
                <span class="body-sm">${Utils.escapeHtml(label)}</span>
                <span class="caption">${clamped}%</span>
            </div>` : ''}
            <div class="progress-bar" role="progressbar" aria-valuenow="${clamped}" aria-valuemin="0" aria-valuemax="100">
                <div class="fill" style="width: ${clamped}%;"></div>
            </div>
        </div>`;
    },

    // ── Empty State ──────────────────────────────────────────────────
    emptyState(icon, message, ctaText = '', ctaHref = '') {
        return `
        <div class="empty-state">
            <div class="icon">${icon}</div>
            <div class="message">${Utils.escapeHtml(message)}</div>
            ${ctaText ? `<a href="${Utils.escapeHtml(ctaHref)}" class="btn-primary cta" style="text-decoration: none;">${Utils.escapeHtml(ctaText)}</a>` : ''}
        </div>`;
    },

    // ── Search Input (with Clear button) ──────────────────────────────
    searchInput(placeholder = 'Search...', id = 'searchInput') {
        return `
        <div class="search-input-wrapper">
            ${Icons.svg('search', {class: 'search-icon'})}
            <input type="text" class="input" id="${id}" placeholder="${Utils.escapeHtml(placeholder)}" autocomplete="off" spellcheck="false">
            <button type="button" class="search-clear-btn" data-for="${id}" aria-label="Clear search">
                ${Icons.svg('x', {class: 'icon-sm'})}
            </button>
        </div>`;
    },

    // ── Select Dropdown ──────────────────────────────────────────────
    select(options, id = 'selectInput', selectedValue = '') {
        const opts = options.map(o => {
            const val = typeof o === 'string' ? o : o.value;
            const label = typeof o === 'string' ? o : o.label;
            const selected = val === selectedValue ? 'selected' : '';
            return `<option value="${Utils.escapeHtml(val)}" ${selected}>${Utils.escapeHtml(label)}</option>`;
        }).join('');
        return `<select class="select" id="${id}">${opts}</select>`;
    },

    // ── Tab Bar ──────────────────────────────────────────────────────
    tabBar(tabs, activeIndex = 0, containerId = 'tabBar') {
        const items = tabs.map((tab, i) =>
            `<button class="tab-item ${i === activeIndex ? 'active' : ''}" data-tab="${i}" role="tab" aria-selected="${i === activeIndex}">${Utils.escapeHtml(tab)}</button>`
        ).join('');
        return `<div class="tab-bar" id="${containerId}" role="tablist">${items}</div>`;
    },

    // ── Code Block (with IntelliJ IDEA Syntax Highlighting & One-Click Copy) ──
    codeBlock(code, language = 'java') {
        const highlighted = Utils.highlightJava(code || '');
        return `
        <div class="code-block-wrapper ij-editor-wrapper">
            <button class="copy-code-btn" data-action="copy-code" aria-label="Copy code to clipboard">
                ${Icons.svg('copy', {class: 'icon-sm'})} Copy
            </button>
            <div class="ij-editor-body">
                ${highlighted}
            </div>
            <pre class="code-block-raw" style="display: none;"><code>${Utils.escapeHtml(code || '')}</code></pre>
        </div>`;
    },

    // ── Loading Skeleton ─────────────────────────────────────────────
    skeleton(width = '100%', height = '20px') {
        return `<div class="skeleton" style="width: ${width}; height: ${height};"></div>`;
    },

    skeletonCard() {
        return `
        <div class="glass-card">
            <div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 12px;"></div>
            <div class="skeleton" style="width: 40%; height: 14px; margin-bottom: 8px;"></div>
            <div class="skeleton" style="width: 80%; height: 14px;"></div>
        </div>`;
    },

    // ── Lecture Card (for Library page) ───────────────────────────────
    lectureCard(lecture, pipelineHash = '') {
        const status = lecture.status || 'new';
        const isOutdated = (status === 'extracted' || status === 'identified' || status === 'matched')
            && lecture.pipeline_hash && lecture.pipeline_hash !== pipelineHash;
        
        const topics = lecture.topics || [];
        const sizeMB = lecture.size_mb ? `${lecture.size_mb.toFixed(0)} MB` : '';
        const parsed = Utils.parseLectureTitle(lecture.title, lecture.num, lecture.filename, lecture.id);

        let actionBtn = '';
        if (status === 'new') {
            actionBtn = `<button class="btn-primary btn-sm" data-action="process" data-id="${Utils.escapeHtml(lecture.id)}">Process</button>`;
        } else if (isOutdated) {
            actionBtn = `<button class="btn-ghost btn-sm" data-action="reprocess" data-id="${Utils.escapeHtml(lecture.id)}">${Icons.svg('refresh-cw', {class: 'icon-sm'})} Re-process</button>`;
        } else if (status === 'transcribed') {
            actionBtn = `<button class="btn-primary btn-sm" data-action="extract" data-id="${Utils.escapeHtml(lecture.id)}">${Icons.svg('sparkles', {class: 'icon-sm'})} Extract</button>`;
        } else {
            actionBtn = `<button class="btn-ghost btn-sm" data-action="rerun" data-id="${Utils.escapeHtml(lecture.id)}">${Icons.svg('refresh-cw', {class: 'icon-sm'})} Re-run</button>`;
        }

        return `
        <div class="lecture-card glass-card" data-lecture-id="${Utils.escapeHtml(lecture.id)}">
            <div class="lecture-main">
                <div class="lecture-info">
                    <div class="lecture-title flex-row gap-sm" style="align-items: center; flex-wrap: wrap;">
                        ${parsed.numStr ? `<span class="lecture-num-pill">${parsed.numStr}</span>` : ''}
                        <span>${Utils.escapeHtml(parsed.topic)}</span>
                        ${parsed.module ? `<span class="lecture-module-pill">${Utils.escapeHtml(parsed.module)}</span>` : ''}
                    </div>
                    <div class="lecture-meta">
                        ${Icons.svg('file-text', {class: 'icon-sm'})}
                        <span>${Utils.escapeHtml(lecture.filename || '')}</span>
                        ${sizeMB ? `<span class="meta-dot">•</span>${Icons.svg('hard-drive', {class: 'icon-sm'})}<span>${sizeMB}</span>` : ''}
                    </div>
                    ${topics.length ? `<div class="lecture-tags">${topics.slice(0, 5).map(t => `<span class="tag-pill">${Utils.escapeHtml(t)}</span>`).join('')}</div>` : ''}
                </div>
                <div class="lecture-controls">
                    <div class="lecture-status-group">
                        ${Components.statusPill(status)}
                        ${isOutdated ? `<span class="status-pill outdated">${Icons.svg('alert-triangle', {class: 'icon-sm'})} Pipeline Updated</span>` : ''}
                    </div>
                    <div class="lecture-actions">
                        ${actionBtn}
                    </div>
                </div>
            </div>
        </div>`;
    },

    // Format and parse raw log lines into clean individual entries with timestamps
    formatLogLines(rawLogs) {
        if (!rawLogs || !Array.isArray(rawLogs)) return [];
        const lines = [];
        rawLogs.forEach(entry => {
            if (!entry) return;
            // Split if entry contains embedded newlines or multiple concatenated [HH:MM:SS] timestamps
            const chunks = String(entry).split(/\r?\n|(?=\[\d{2}:\d{2}:\d{2}\])/g);
            chunks.forEach(c => {
                const trimmed = c.trim();
                if (trimmed) lines.push(trimmed);
            });
        });
        return lines;
    },

    // ── Dedicated Active Pipeline Command Card ───────────────────────
    activePipelineCard(jobStatus, lecture) {
        const progress = jobStatus?.progress || 0;
        const stepName = jobStatus?.step_name || 'Initializing pipeline...';
        const rawLogs = jobStatus?.logs || [];
        const lines = Components.formatLogLines(rawLogs);
        const parsed = Utils.parseLectureTitle(lecture?.title, lecture?.num, lecture?.filename, lecture?.id);

        let currentStep = 1;
        const sLower = stepName.toLowerCase();
        if (sLower.includes('extract') || sLower.includes('concept')) {
            currentStep = 2;
        } else if (sLower.includes('identif') || sLower.includes('match') || sLower.includes('mcq') || sLower.includes('complete')) {
            currentStep = 3;
        }

        const logRows = lines.map(line => {
            const timeMatch = line.match(/^(\[\d{2}:\d{2}:\d{2}\])\s*(.*)$/);
            if (timeMatch) {
                return `<div class="terminal-row"><span class="log-timestamp">${Utils.escapeHtml(timeMatch[1])}</span> <span class="log-text">${Utils.escapeHtml(timeMatch[2])}</span></div>`;
            }
            return `<div class="terminal-row"><span class="log-text">${Utils.escapeHtml(line)}</span></div>`;
        }).join('');

        return `
        <div class="active-pipeline-card" data-lecture-id="${Utils.escapeHtml(lecture.id)}">
            <div class="pipeline-card-header">
                <div class="pipeline-lecture-info">
                    <span class="processing-pulse-dot"></span>
                    <div class="flex-row gap-sm" style="align-items: center; flex-wrap: wrap;">
                        ${parsed.numStr ? `<span class="lecture-num-pill" style="color: var(--color-accent-blue); border-color: rgba(59,158,255,0.4); background: rgba(59,158,255,0.1);">${parsed.numStr}</span>` : ''}
                        <span class="pipeline-lecture-title">${Utils.escapeHtml(parsed.topic)}</span>
                        ${parsed.module ? `<span class="lecture-module-pill">${Utils.escapeHtml(parsed.module)}</span>` : ''}
                    </div>
                </div>

                <div class="pipeline-header-actions">
                    <button class="btn-ghost btn-sm log-toggle-btn" data-action="toggle-log" data-id="${Utils.escapeHtml(lecture.id)}" aria-expanded="true">
                        ${Icons.svg('terminal', {class: 'icon-xs'})}
                        <span class="toggle-log-text">Hide Logs</span>
                        ${Icons.svg('chevron-up', {class: 'icon-xs toggle-chevron'})}
                    </button>
                    <button class="btn-ghost btn-sm pipeline-cancel-btn" data-action="cancel" data-id="${Utils.escapeHtml(lecture.id)}" title="Cancel processing pipeline">
                        ${Icons.svg('x-circle', {class: 'icon-xs'})} Cancel Pipeline
                    </button>
                </div>
            </div>

            <!-- 3-Segment Visual Step Stepper -->
            <div class="pipeline-stepper-bar">
                <div class="pipeline-step-item ${currentStep >= 1 ? (currentStep === 1 ? 'active' : 'completed') : ''}" data-step="1">
                    <span class="step-num">${currentStep > 1 ? Icons.svg('check', {class: 'icon-xs'}) : '1'}</span>
                    <span class="step-label">Whisper Audio</span>
                </div>
                <div class="pipeline-step-connector ${currentStep > 1 ? 'completed' : ''}" data-connector="1"></div>
                <div class="pipeline-step-item ${currentStep >= 2 ? (currentStep === 2 ? 'active' : 'completed') : ''}" data-step="2">
                    <span class="step-num">${currentStep > 2 ? Icons.svg('check', {class: 'icon-xs'}) : '2'}</span>
                    <span class="step-label">Concept Extraction</span>
                </div>
                <div class="pipeline-step-connector ${currentStep > 2 ? 'completed' : ''}" data-connector="2"></div>
                <div class="pipeline-step-item ${currentStep >= 3 ? (currentStep === 3 ? 'active' : 'completed') : ''}" data-step="3">
                    <span class="step-num">3</span>
                    <span class="step-label">Problem Matching</span>
                </div>
            </div>

            <!-- Progress status & percentage bar -->
            <div class="pipeline-progress-meta">
                <div class="flex-row gap-sm" style="align-items: center;">
                    <span class="step-spinner"></span>
                    <span class="pipeline-current-step-text">${Utils.escapeHtml(stepName)}</span>
                </div>
                <span class="pipeline-progress-percentage">${Math.round(progress)}%</span>
            </div>

            <div class="progress-bar-track">
                <div class="progress-bar-fill" style="width: ${Math.round(progress)}%;"></div>
            </div>

            <!-- Live Terminal Stream with Header -->
            <div class="log-container" id="logContainer-${Utils.escapeHtml(lecture.id)}">
                <div class="terminal-console">
                    <div class="terminal-topbar">
                        <div class="terminal-dots">
                            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                        </div>
                        <span class="terminal-title">live stream console</span>
                    </div>
                    <div class="log-output">${logRows}</div>
                </div>
            </div>
        </div>`;
    },

    // ── Processing Card (for inline panels) ──
    processingPanel(jobStatus, lectureId = '') {
        const progress = jobStatus.progress || 0;
        const stepName = jobStatus.step_name || 'Processing';
        const rawLogs = jobStatus.logs || [];
        const lines = Components.formatLogLines(rawLogs);

        const logRows = lines.map(line => {
            const timeMatch = line.match(/^(\[\d{2}:\d{2}:\d{2}\])\s*(.*)$/);
            if (timeMatch) {
                return `<div class="terminal-row"><span class="log-timestamp">${Utils.escapeHtml(timeMatch[1])}</span> <span class="log-text">${Utils.escapeHtml(timeMatch[2])}</span></div>`;
            }
            return `<div class="terminal-row"><span class="log-text">${Utils.escapeHtml(line)}</span></div>`;
        }).join('');

        return `
        <div class="terminal-console" style="margin-top: 10px;">
            <div class="terminal-topbar">
                <div class="step-indicator">
                    <span class="step-spinner"></span>
                    <span class="pipeline-current-step-text">${Utils.escapeHtml(stepName)}</span>
                    <span class="pipeline-progress-percentage">${Math.round(progress)}%</span>
                </div>
                <button class="btn-ghost btn-sm log-toggle-btn" data-action="toggle-log" data-id="${Utils.escapeHtml(lectureId)}" aria-expanded="true">
                    ${Icons.svg('terminal', {class: 'icon-xs'})}
                    <span class="toggle-log-text">Hide Logs</span>
                    ${Icons.svg('chevron-up', {class: 'icon-xs toggle-chevron'})}
                </button>
            </div>
            <div class="progress-bar-track" style="margin-bottom: 0; border-radius: 0; border-left: none; border-right: none;">
                <div class="progress-bar-fill" style="width: ${Math.round(progress)}%;"></div>
            </div>
            <div class="log-container" id="logContainer-${Utils.escapeHtml(lectureId)}">
                <div class="log-output">${logRows}</div>
            </div>
        </div>`;
    },

    // ── Problem Overview Card (Problem-First Focal Architecture) ─────
    problemOverviewCard(problem, index, matchedProblem = null) {
        const desc = problem.description || 'Problem discussed in lecture';
        const approach = problem.approach || '';
        const trick = problem.core_trick || '';
        const code = problem.code_reconstruction || '';
        const ts = problem.timestamp_range || [];
        const numStr = String(index + 1).padStart(2, '0');

        return `
        <div class="problem-overview-card stagger-card" data-problem-index="${index}" tabindex="0" role="button" aria-label="View problem ${index + 1}">
            <!-- Main Hero Problem Line -->
            <div class="card-problem-main">
                <span class="problem-index-num">${numStr}.</span>
                <h3 class="problem-statement-text">${Utils.escapeHtml(desc)}</h3>
            </div>

            <!-- Supporting Insight / Intuition Preview -->
            ${trick || approach ? `
            <div class="card-trick-preview">
                <span class="trick-label">Insight:</span> <span class="trick-text">${Utils.escapeHtml(trick || approach)}</span>
            </div>` : ''}

            <!-- Muted Secondary Footer Strip -->
            <div class="card-footer-strip">
                <div class="card-meta-inline">
                    ${ts.length === 2 ? `<span class="meta-item">${Icons.svg('clock', {class: 'icon-xs'})} ${Utils.escapeHtml(ts[0])} — ${Utils.escapeHtml(ts[1])}</span>` : ''}
                    ${matchedProblem?.difficulty ? `<span class="meta-dot">•</span><span class="meta-item ${matchedProblem.difficulty.toLowerCase()}">${Utils.escapeHtml(matchedProblem.difficulty)}</span>` : ''}
                    ${matchedProblem?.platform ? `<span class="meta-item muted">${Utils.escapeHtml(matchedProblem.platform)}</span>` : ''}
                    ${code ? `<span class="meta-dot">•</span><span class="meta-item">${Icons.svg('code', {class: 'icon-xs'})} Java</span>` : ''}
                </div>

                <div class="explore-action">
                    <span>View Solution</span>
                    ${Icons.svg('arrow-right', {class: 'icon-xs explore-arrow'})}
                </div>
            </div>
        </div>`;
    },

    // ── Full Problem Detail View (Unified High-Craft Problem Workspace) ─
    problemDetailView(problem, index, totalProblems, lecture, matchedProblem = null, isSolved = false) {
        const desc = problem.description || 'Problem discussed in lecture';
        const approach = problem.approach || '';
        const trick = problem.core_trick || '';
        const code = problem.code_reconstruction || '';
        const ts = problem.timestamp_range || [];
        const inputFormat = problem.input_format || '';
        const outputFormat = problem.output_format || '';
        const numStr = String(index + 1).padStart(2, '0');

        let searchUrl = '';
        if (matchedProblem) {
            searchUrl = Utils.googleSearchUrl(matchedProblem.title, matchedProblem.platform);
        } else {
            searchUrl = Utils.googleSearchUrl(desc.slice(0, 60), 'LeetCode');
        }

        const prevDisabled = index === 0;
        const nextDisabled = index >= totalProblems - 1;

        return `
        <div class="problem-detail-container stagger-in">
            <!-- Top Command & Action Bar (Unboxed Seamless Breadcrumb Strip) -->
            <div class="problem-command-bar">
                <div class="command-bar-left">
                    <div class="flex-row gap-sm" style="align-items: center; flex-wrap: wrap;">
                        <span style="font-family: var(--font-mono); font-size: 12.5px; font-weight: 700; color: #e2e8f0;">Problem ${numStr} <span style="color: #64748b; font-weight: 500;">/ ${String(totalProblems).padStart(2, '0')}</span></span>
                        ${ts.length === 2 ? `<span style="display: inline-flex; align-items: center; gap: 4px; font-family: var(--font-mono); font-size: 11px; color: #94a3b8; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 2px 7px; border-radius: 4px;">${Icons.svg('clock', {class: 'icon-xs'})} ${Utils.escapeHtml(ts[0])} — ${Utils.escapeHtml(ts[1])}</span>` : ''}
                        ${matchedProblem ? Components.difficultyBadge(matchedProblem.difficulty) : '<span style="font-size: 11px; font-family: var(--font-mono); color: #93c5fd; background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); padding: 2px 7px; border-radius: 4px;">Lecture Discussion</span>'}
                    </div>
                </div>

                <div class="command-bar-right">
                    <button type="button" class="btn-ghost btn-sm ${isSolved ? 'active' : ''}" data-action="toggle-solved" data-problem-idx="${index}" style="${isSolved ? 'color: var(--color-accent-green); border-color: rgba(17,255,153,0.4); background: rgba(17,255,153,0.08);' : 'color: #cbd5e1; border-color: rgba(255,255,255,0.1);'}">
                        ${Icons.svg(isSolved ? 'check-circle' : 'circle', {class: 'icon-sm'})} ${isSolved ? 'Solved' : 'Mark Solved'}
                    </button>
                    <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" class="btn-ghost btn-sm" style="color: #cbd5e1; border-color: rgba(255,255,255,0.1);" title="Search problem online">
                        ${Icons.svg('external-link', {class: 'icon-sm'})} Search Online
                    </a>
                </div>
            </div>

            <!-- Problem Hero Statement Card -->
            <div class="problem-statement-card">
                <h1 class="problem-hero-title">
                    ${Utils.escapeHtml(desc)}
                </h1>

                ${(inputFormat || outputFormat) ? `
                <div class="problem-io-strip">
                    ${inputFormat ? `
                    <div class="io-item">
                        <span class="io-tag">Input Format</span>
                        <div class="io-content">${Utils.escapeHtml(inputFormat)}</div>
                    </div>` : ''}
                    ${outputFormat ? `
                    <div class="io-item">
                        <span class="io-tag">Output Format</span>
                        <div class="io-content">${Utils.escapeHtml(outputFormat)}</div>
                    </div>` : ''}
                </div>` : ''}
            </div>

            <!-- Core Trick & Intuition Banner -->
            ${trick ? `
            <div class="strategy-callout-card trick">
                <div class="callout-header">
                    ${Icons.svg('zap', {class: 'icon-sm callout-icon'})}
                    <span>Core Trick & Algorithmic Intuition</span>
                </div>
                <div class="callout-body">
                    ${Utils.escapeHtml(trick)}
                </div>
            </div>` : ''}

            <!-- Step-by-Step Approach Card -->
            ${approach ? `
            <div class="strategy-callout-card approach">
                <div class="callout-header">
                    ${Icons.svg('compass', {class: 'icon-sm callout-icon'})}
                    <span>Step-by-Step Approach & Reasoning</span>
                </div>
                <div class="callout-body">
                    ${Utils.escapeHtml(approach)}
                </div>
            </div>` : ''}

            <!-- Reconstructed Code Section (IntelliJ IDEA Theme) -->
            ${code ? `
            <div class="code-editor-card ij-editor-window">
                <div class="editor-topbar ij-topbar">
                    <div class="ij-tab-group">
                        <div class="editor-tab ij-active-tab">
                            <span class="ij-file-icon" style="display: inline-flex; align-items: center; justify-content: center; width: 15px; height: 15px; background: #3574f0; color: #fff; font-weight: 700; font-size: 9.5px; border-radius: 3px; font-family: var(--font-sans-ui);">C</span>
                            <span class="ij-tab-filename">Solution.java</span>
                            <span class="ij-tab-close">✕</span>
                        </div>
                    </div>
                    <div class="editor-meta ij-meta">
                        <span class="caption" style="font-size: 11px; color: #7a7e85; font-family: var(--font-mono);">Java 17 (OpenJDK)</span>
                    </div>
                </div>
                ${Components.codeBlock(code, 'java')}
            </div>` : `
            <div class="glass-card" style="padding: 1.5rem; text-align: center; color: var(--color-ash);">
                ${Icons.svg('file-text', {class: 'icon-lg', style: 'margin-bottom: 8px;'})}
                <div class="body-sm">This problem was discussed verbally and conceptually in the lecture.</div>
            </div>`}

            <!-- Matched Online Problem Link Banner (if matched) -->
            ${matchedProblem ? `
            <div class="matched-problem-banner">
                <div class="flex-row gap-sm" style="align-items: center;">
                    ${Icons.svg('check-circle-2', {class: 'icon-md', style: 'color: var(--color-accent-green); flex-shrink: 0;'})}
                    <div>
                        <div class="body-sm" style="font-weight: 600; color: var(--color-ink);">
                            Matched on ${Utils.escapeHtml(matchedProblem.platform || 'LeetCode')}: <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" style="color: var(--color-accent-blue); text-decoration: underline;">${Utils.escapeHtml(matchedProblem.title)}</a>
                        </div>
                        <div class="caption" style="font-size: 11px;">Practice this identical problem directly on the platform.</div>
                    </div>
                </div>
                <div class="flex-row gap-sm" style="align-items: center;">
                    ${Components.difficultyBadge(matchedProblem.difficulty)}
                    <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" class="btn-ghost btn-sm">
                        ${Icons.svg('external-link', {class: 'icon-sm'})} Open Problem
                    </a>
                </div>
            </div>` : ''}

            <!-- Problem Solving Methodology Checklist Drawer -->
            <div style="margin-top: 4px;">
                ${Components.methodologyChecklist(matchedProblem?.problem_id || `${lecture.id}-p${index}`, { embedded: true, defaultOpen: false, title: `Problem Solving Methodology · Problem ${numStr}` })}
            </div>

            <!-- Bottom Navigation Bar -->
            <div class="problem-nav-footer" style="display: flex; justify-content: center;">
                <button type="button" class="btn-ghost btn-sm" data-action="back-to-overview">
                    ${Icons.svg('grid', {class: 'icon-sm'})} Back to All Questions in Lecture
                </button>
            </div>
        </div>`;
    },

    // Legacy compatibility problemCard
    problemCard(problem, matchedProblem = null) {
        return this.problemOverviewCard(problem, 0, matchedProblem);
    },

    // ── MCQ Card ─────────────────────────────────────────────────────
    mcqCard(question, index, lectureId) {
        const q = question.question || '';
        const options = question.options || [];
        const qId = `mcq-${lectureId}-${index}`;
        const numStr = String(index + 1).padStart(2, '0');

        const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
        const optionsHtml = options.map((opt, i) => `
            <div class="mcq-option" data-index="${i}" data-qid="${qId}" tabindex="0" role="radio" aria-checked="false">
                <span class="option-key">${letters[i] || (i + 1)}</span>
                <span class="option-text">${Utils.escapeHtml(opt)}</span>
            </div>
        `).join('');

        return `
        <div class="mcq-card glass-card" id="${qId}" data-answer="${question.answer_idx || 0}">
            <div class="question-header">
                <span class="question-badge">Q${numStr}</span>
                <div class="question-text">${Utils.escapeHtml(q)}</div>
            </div>
            <div class="mcq-options" role="radiogroup">${optionsHtml}</div>
            <div class="mcq-actions">
                <button class="btn-primary btn-sm" data-action="check-mcq" data-qid="${qId}">
                    ${Icons.svg('check', {class: 'icon-sm'})} Check Answer
                </button>
            </div>
            <div class="mcq-feedback" style="display: none;"></div>
        </div>`;
    },

    // ── Lecture Picker Modal (for Practice Sheets Hub) ────────────────
    lecturePickerModal(lectures, selectedLectureId = '') {
        const lectureListHtml = lectures.map(l => {
            const isSelected = l.id === selectedLectureId;
            const parsed = Utils.parseLectureTitle(l.title, l.num, l.filename, l.id);
            const mcqCnt = (l.mcqs || []).length;
            const ladderCnt = (l.concept_ladder || []).length;
            const probCnt = Array.isArray(l.problems_discussed) ? l.problems_discussed.length : 0;

            return `
            <div class="picker-modal-item ${isSelected ? 'selected' : ''}" data-lecture-id="${Utils.escapeHtml(l.id)}" tabindex="0" role="button">
                <div class="flex-row gap-sm" style="align-items: center; min-width: 0;">
                    ${parsed.numStr ? `<span class="lecture-num-pill">${parsed.numStr}</span>` : ''}
                    <div style="min-width: 0; flex: 1;">
                        <div class="body-sm" style="font-weight: 600; color: ${isSelected ? 'var(--color-accent-green)' : 'var(--color-ink)'}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${Utils.escapeHtml(parsed.topic)}
                        </div>
                        ${parsed.module ? `<div class="caption" style="font-size: 11px;">${Utils.escapeHtml(parsed.module)}</div>` : ''}
                    </div>
                </div>
                <div class="flex-row gap-sm" style="align-items: center; flex-shrink: 0;">
                    ${mcqCnt ? `<span class="badge-pill" style="font-size: 10.5px;">${mcqCnt} MCQs</span>` : ''}
                    ${ladderCnt ? `<span class="badge-pill" style="font-size: 10.5px;">${ladderCnt} Steps</span>` : ''}
                    ${isSelected ? Icons.svg('check', {class: 'icon-sm', style: 'color: var(--color-accent-green);'}) : ''}
                </div>
            </div>`;
        }).join('');

        return `
        <div class="modal" style="max-width: 620px; width: 95%;">
            <div class="modal-header">
                <h3 class="heading-md flex-row gap-sm" style="align-items: center;">
                    ${Icons.svg('book-open', {class: 'icon-md', style: 'color: var(--color-accent-blue);'})} Select Practice Lecture
                </h3>
                <button class="btn-icon modal-close" data-action="close-modal" aria-label="Close dialog">${Icons.svg('x', {class: 'icon-md'})}</button>
            </div>
            
            <div style="margin-bottom: 1rem;">
                <div class="search-input-wrapper">
                    <span class="search-icon">${Icons.svg('search', {class: 'icon-sm'})}</span>
                    <input type="text" class="input" id="modalLectureSearch" placeholder="Search by lecture name, number, or module..." autocomplete="off">
                </div>
            </div>

            <div class="picker-modal-list" id="pickerModalList" style="max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; padding-right: 4px;">
                ${lectureListHtml}
            </div>
        </div>`;
    },

    // ── Concept Ladder Step ──────────────────────────────────────────
    ladderStep(step, index, isSolved = false) {
        const title = step.title || `Step ${index + 1}`;
        const diff = step.difficulty || 'Medium';
        const why = step.why_this_problem || '';
        const searchUrl = Utils.googleSearchUrl(title, step.platform || 'LeetCode');

        return `
        <div class="ladder-step ${isSolved ? 'completed' : ''}">
            <div class="step-node ${isSolved ? 'completed' : ''}">
                ${isSolved ? Icons.svg('check', {class: 'icon-xs'}) : `<span class="step-number">${index + 1}</span>`}
            </div>
            <div class="step-content glass-card">
                <div class="flex-between">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        ${isSolved ? Icons.svg('check-circle-2', {class: 'icon-md diff-easy'}) : Icons.svg('circle', {class: 'icon-md caption'})}
                        <span class="body-md"><strong>${Utils.escapeHtml(title)}</strong></span>
                        ${Components.difficultyBadge(diff)}
                    </div>
                    <button class="btn-ghost btn-sm" data-action="log-attempt" data-problem="${Utils.escapeHtml(step.id || title)}">${Icons.svg('bar-chart-2', {class: 'icon-sm'})} Log</button>
                </div>
                <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" class="body-sm flex-row gap-sm problem-search-link" style="margin-top: 8px; display: inline-flex;">
                    ${Icons.svg('search', {class: 'icon-sm'})} Search on ${Utils.escapeHtml(step.platform || 'LeetCode')}
                </a>
                ${why ? `<div class="caption flex-row gap-sm" style="margin-top: 6px; align-items: flex-start;">${Icons.svg('lightbulb', {class: 'icon-sm', style: 'flex-shrink: 0'})} <span>${Utils.escapeHtml(why)}</span></div>` : ''}
            </div>
        </div>`;
    },

    // ── Activity Item (Dashboard) ────────────────────────────────────
    activityItem(attempt, problemTitle = '') {
        const solved = attempt.solved;
        const icon = solved ? Icons.svg('check', {class: 'icon-md'}) : Icons.svg('x', {class: 'icon-md'});
        const iconClass = solved ? 'solved' : 'failed';
        const date = Utils.formatDate(attempt.date);
        const time = attempt.time_min || 0;
        const diff = attempt.difficulty_felt || 3;
        const stars = '★'.repeat(diff) + '☆'.repeat(5 - diff);
        const hint = attempt.used_hint ? ` • ${Icons.svg('lightbulb', {class: 'icon-sm'})} Hint` : '';

        return `
        <div class="activity-item">
            <div class="status-icon ${iconClass}">${icon}</div>
            <div class="activity-info">
                <div class="body-md">${Utils.escapeHtml(problemTitle || attempt.problem_id)}</div>
                <div class="activity-meta">${date} • ${time}min • ${stars}${hint}</div>
            </div>
        </div>`;
    },

    // ── Review Card (Dashboard) ──────────────────────────────────────
    reviewCard(review) {
        const pattern = review.pattern || 'Unknown';
        const interval = review.interval || 1;
        const ef = review.ease_factor ? review.ease_factor.toFixed(1) : '2.5';
        const prob = review.recommended_problem;
        const isOverdue = review.interval <= 0 || (review.next_review && new Date(review.next_review) <= new Date());

        let problemHtml = '';
        if (prob) {
            const searchUrl = Utils.googleSearchUrl(prob.title, prob.platform);
            problemHtml = `
            <div style="margin-top: 8px;">
                <span class="body-sm">→ Practice: </span>
                <a href="${Utils.escapeHtml(searchUrl)}" target="_blank" rel="noopener" class="problem-search-link">
                    <strong>${Utils.escapeHtml(prob.title)}</strong>
                </a>
                ${Components.difficultyBadge(prob.difficulty)}
            </div>`;
        }

        return `
        <div class="review-card glass-card ${isOverdue ? 'overdue' : ''}">
            <div class="flex-between">
                <div>
                    <div class="pattern-name flex-row gap-sm">
                        ${Icons.svg('repeat', {class: 'icon-sm'})} ${Utils.escapeHtml(pattern)}
                        ${isOverdue ? `<span class="badge-pill" style="font-size: 10px; color: var(--color-accent-red); border-color: rgba(255, 32, 71, 0.3);">Due Now</span>` : ''}
                    </div>
                    ${problemHtml}
                </div>
                <button class="btn-ghost btn-sm flex-row gap-sm" data-action="log-revision" data-pattern="${Utils.escapeHtml(pattern)}" ${prob ? `data-problem-id="${Utils.escapeHtml(prob.id)}"` : ''}>
                    ${Icons.svg('bar-chart-2', {class: 'icon-sm'})} Log
                </button>
            </div>
            <div class="review-meta" style="margin-top: 10px;">
                <span>Interval: ${interval.toFixed(0)}d</span>
                <span>EF: ${ef}</span>
                <span>Reps: ${review.repetitions || 0}</span>
            </div>
        </div>`;
    },

    // ── Attempt Log Modal ────────────────────────────────────────────
    attemptModal(title, problemId) {
        return `
        <div class="modal">
            <div class="modal-header">
                <h3 class="heading-md">Log Attempt</h3>
                <button class="btn-icon modal-close" data-action="close-modal" aria-label="Close dialog">${Icons.svg('x', {class: 'icon-md'})}</button>
            </div>
            <div class="body-sm" style="margin-bottom: 1.5rem;">
                <strong>${Utils.escapeHtml(title)}</strong>
            </div>
            <form id="attemptForm" data-problem-id="${Utils.escapeHtml(problemId)}">
                <div class="grid-2 gap-md" style="margin-bottom: 1rem;">
                    <label class="flex-col gap-sm">
                        <span class="caption">Solved?</span>
                        <label class="flex-row gap-sm" style="cursor: pointer;">
                            <input type="checkbox" id="attemptSolved" style="accent-color: var(--color-accent-green); width: 16px; height: 16px;"> 
                            <span class="body-sm">Yes, I solved it</span>
                        </label>
                    </label>
                    <label class="flex-col gap-sm">
                        <span class="caption">Used Hint?</span>
                        <label class="flex-row gap-sm" style="cursor: pointer;">
                            <input type="checkbox" id="attemptHint" style="accent-color: var(--color-accent-yellow); width: 16px; height: 16px;">
                            <span class="body-sm">Yes</span>
                        </label>
                    </label>
                </div>
                <div class="grid-2 gap-md" style="margin-bottom: 1rem;">
                    <label class="flex-col gap-sm">
                        <div class="flex-between">
                            <span class="caption">Difficulty Felt (1-5)</span>
                            <span class="badge-pill" id="difficultyDisplay" style="font-size: 11px;">Level 3</span>
                        </div>
                        <input type="range" id="attemptDifficulty" min="1" max="5" value="3" style="margin-top: 6px;">
                    </label>
                    <label class="flex-col gap-sm">
                        <span class="caption">Time (minutes)</span>
                        <input type="number" class="input" id="attemptTime" min="0" value="15" style="height: 38px;">
                    </label>
                </div>
                <label class="flex-col gap-sm" style="margin-bottom: 1.5rem;">
                    <span class="caption">Notes (optional)</span>
                    <textarea class="input" id="attemptNotes" rows="2" placeholder="Any observations or key insights..."></textarea>
                </label>
                <div class="flex-row" style="justify-content: flex-end; gap: 8px;">
                    <button type="button" class="btn-ghost" data-action="close-modal">Cancel</button>
                    <button type="submit" class="btn-primary">${Icons.svg('save', {class: 'icon-sm'})} Save Attempt</button>
                </div>
            </form>
        </div>`;
    },

    // ── Coverage Table Row ───────────────────────────────────────────
    coverageRow(pattern, solved, total) {
        const pct = total > 0 ? Math.round((solved / total) * 100) : 0;
        const barColor = pct >= 75 ? 'var(--color-accent-green)' : pct >= 40 ? 'var(--color-accent-yellow)' : 'var(--color-accent-red)';

        return `
        <tr>
            <td class="body-sm"><strong>${Utils.escapeHtml(pattern)}</strong></td>
            <td class="caption" style="text-align: center;">${solved}</td>
            <td class="caption" style="text-align: center;">${total}</td>
            <td>
                <div class="flex-row gap-sm" style="align-items: center;">
                    <div class="coverage-bar" style="width: ${pct}%; background: ${barColor}; max-width: 120px;"></div>
                    <span class="caption">${pct}%</span>
                </div>
            </td>
        </tr>`;
    },

    // ── Section Header ───────────────────────────────────────────────
    sectionHeader(title, rightContent = '', icon = '') {
        const iconHtml = icon ? Icons.svg(icon, {class: 'icon-md', style: 'margin-right: 8px; vertical-align: -2px;'}) : '';
        const titleStr = typeof title === 'string' ? title : '';
        const isHtml = titleStr.includes('<svg') || titleStr.includes('<i');
        const titleContent = isHtml ? titleStr : `${iconHtml}${Utils.escapeHtml(titleStr)}`;
        return `
        <div class="flex-between section-header" style="margin-bottom: 1rem;">
            <h2 class="heading-lg" style="display: flex; align-items: center;">${titleContent}</h2>
            ${rightContent ? `<div>${rightContent}</div>` : ''}
        </div>`;
    },

    // ── Cancel Confirm Modal ─────────────────────────────────────────
    cancelConfirmModal(lectureTitle, lectureId) {
        return `
        <div class="modal">
            <div class="modal-header">
                <h3 class="heading-md" style="color: var(--color-accent-red); display: flex; align-items: center; gap: 8px;">
                    ${Icons.svg('alert-triangle', {class: 'icon-md'})} Cancel Processing
                </h3>
                <button class="btn-icon modal-close" data-action="close-modal" aria-label="Close dialog">${Icons.svg('x', {class: 'icon-md'})}</button>
            </div>
            <div class="body-md" style="margin-bottom: 1rem;">
                Are you sure you want to cancel processing for <strong>${Utils.escapeHtml(lectureTitle)}</strong>?
            </div>
            <div class="body-sm" style="margin-bottom: 1.5rem; color: var(--color-ash);">
                This will stop the processing pipeline and discard all progress. The lecture will be reset to its original state.
            </div>
            <div class="flex-row" style="justify-content: flex-end; gap: 8px;">
                <button type="button" class="btn-ghost" data-action="close-modal">Continue Processing</button>
                <button type="button" class="btn-danger" id="confirmCancelBtn" data-id="${Utils.escapeHtml(lectureId)}">Cancel Processing</button>
            </div>
        </div>`;
    },

    // ── Systematic DSA Problem-Solving Methodology Framework ─────────────────
    methodologyChecklist(problemId = '', options = {}) {
        const scope = problemId || 'global';
        const title = options.title || 'Systematic DSA Problem-Solving Framework';
        const isEmbedded = options.embedded === true;
        const defaultOpen = options.defaultOpen === true;

        // Structured Stages (7 Total: 6 Core Stages + Live Interview Protocol)
        const stages = [
            {
                id: 'stage1',
                num: '01',
                title: 'Problem Deconstruction & Constraint Decoupling',
                badge: 'Analysis & Bounds',
                summary: 'Clarify problem ambiguity and translate input constraints into target complexity bounds before choosing an algorithm.',
                items: [
                    {
                        id: 's1_io',
                        label: 'Input / Output & Edge Case Checks',
                        desc: 'Verify types, 0-indexed vs 1-indexed, empty/null cases, single elements, negative values, and duplicates.',
                        tip: 'Edge cases: single node, duplicates, overflow on summation, extreme bounds.'
                    },
                    {
                        id: 's1_constraints',
                        label: 'Map Constraints to Maximum Allowed Time Complexity',
                        desc: 'Use input size N to calculate target runtime complexity and rule out non-viable algorithmic paradigms.',
                        hasTable: 'constraints'
                    }
                ]
            },
            {
                id: 'stage2',
                num: '02',
                title: 'Formulate the Brute-Force Baseline',
                badge: 'Baseline Anchor',
                summary: 'Always articulate the naive baseline solution first before attempting complex optimizations.',
                items: [
                    {
                        id: 's2_validate',
                        label: 'Validate Problem Understanding',
                        desc: 'Confirm you have grasped the core objective, problem constraints, and output invariants.'
                    },
                    {
                        id: 's2_anchor',
                        label: 'Establish Correctness Anchor',
                        desc: 'Provides a reference baseline against which you can verify outputs and behavior of optimized solutions.'
                    },
                    {
                        id: 's2_paralysis',
                        label: 'Prevent Interview Paralysis',
                        desc: 'Articulate baseline approach and exact time/space complexities (e.g. O(N²) / O(2ⁿ)) to secure a working baseline.'
                    }
                ]
            },
            {
                id: 'stage3',
                num: '03',
                title: 'Spot Redundancy & Optimize Iteratively',
                badge: 'Pattern Optimization',
                summary: 'Optimization is the systematic elimination of repeated computations. Ask: "Where is the baseline wasting time?"',
                items: [
                    {
                        id: 's3_bottleneck',
                        label: 'Pinpoint Computational Bottlenecks',
                        desc: 'Identify nested iterations, repeated linear scans, or redundant subproblem evaluations.'
                    },
                    {
                        id: 's3_patterns',
                        label: 'Apply Canonical Optimization Techniques',
                        desc: 'Match identified computational bottleneck to optimal algorithmic paradigm / data structure.',
                        hasTable: 'bottlenecks'
                    }
                ]
            },
            {
                id: 'stage4',
                num: '04',
                title: 'Pen-and-Paper Dry Run (Prior to Coding)',
                badge: 'Pre-Coding Verification',
                summary: 'Catching logic bugs on paper takes seconds; debugging in code during an interview takes 20 minutes.',
                items: [
                    {
                        id: 's4_tracing',
                        label: 'Manual State Tracing',
                        desc: 'Take a realistic, non-trivial test case (not just sample 1). Step-trace pointers, loop variables, accumulators, stacks/queues, and visited arrays.'
                    },
                    {
                        id: 's4_boundary',
                        label: 'Verify Boundary & Base Conditions',
                        desc: 'Check loop termination (left < right vs left <= right), base cases in recursion, and potential off-by-one errors.'
                    },
                    {
                        id: 's4_pseudocode',
                        label: 'Write Structured Pseudocode Outline',
                        desc: 'Map out helper functions, data structure operations, and core logic blocks before syntax translation.'
                    }
                ]
            },
            {
                id: 'stage5',
                num: '05',
                title: 'Production-Grade Implementation & Complexity Defense',
                badge: 'Engineering Rigor',
                summary: 'Write clean, modular code adhering to software engineering best practices and defend asymptotic bounds.',
                items: [
                    {
                        id: 's5_naming',
                        label: 'Self-Documenting Variable Naming',
                        desc: 'Use descriptive identifiers (e.g., windowStart, maxProfit, prevNode, currSum) rather than cryptic single letters.'
                    },
                    {
                        id: 's5_edge',
                        label: 'Defensive Edge-Case Handling',
                        desc: 'Guard against null pointers, empty collections, and 32-bit integer overflow (use 64-bit integers or modulo 1e9+7 when specified).'
                    },
                    {
                        id: 's5_proof',
                        label: 'Explicit Complexity Proof',
                        desc: 'Clearly articulate Time Complexity (Best, Average, Worst) and Auxiliary Space (differentiating input memory from recursion stack / heap allocations).'
                    }
                ]
            },
            {
                id: 'stage6',
                num: '06',
                title: 'Post-Solve Reflection & Deliberate Practice Rules',
                badge: 'Retention & Recall',
                summary: 'Build long-term algorithmic retention and mastery through structured reflection.',
                items: [
                    {
                        id: 's6_rule1',
                        label: 'The 30-Minute Struggle Rule',
                        desc: 'Never check the solution in the first 30–45 minutes. The mental struggle of being stuck is where problem-solving neural pathways form.'
                    },
                    {
                        id: 's6_rule2',
                        label: 'Classify by Canonical Patterns',
                        desc: 'Categorize into patterns: Two Pointers, Fast & Slow, Monotonic Stack, Top-K Heaps, Interval Merging, Tree Traversals, Graph BFS/DFS, DP on Subsequences.'
                    },
                    {
                        id: 's6_rule3',
                        label: 'Active Recall & Spaced Repetition',
                        desc: 'Maintain a structured problem repository. Flag hard or insightful problems and re-solve them from scratch without looking at prior solutions 2 to 3 weeks later.'
                    }
                ]
            },
            {
                id: 'stage_bonus',
                num: '07',
                title: 'Live Interview Communication Protocol',
                badge: 'Think Out Loud',
                summary: 'Technical interviews evaluate structured communication, trade-off analysis, and proactive verification alongside coding.',
                isBonus: true,
                items: [
                    {
                        id: 'sb_initial',
                        label: 'Initial 5 Mins (Deconstruction)',
                        desc: 'Restate the problem in your own words. Confirm edge cases and clarify constraints before speaking algorithms.'
                    },
                    {
                        id: 'sb_pitch',
                        label: 'Algorithm Pitch & Trade-Offs',
                        desc: 'Propose brute force → state time/space → pitch optimal approach & trade-offs → wait for interviewer nod.'
                    },
                    {
                        id: 'sb_during',
                        label: 'During Coding (Narrative Execution)',
                        desc: 'Narrate what each block accomplishes. Avoid long silent pauses; explain why you choose specific data structures.'
                    },
                    {
                        id: 'sb_post',
                        label: 'Post-Coding (Verification)',
                        desc: 'Dry run a test case out loud pointing out variable changes before declaring completion. State final complexities.'
                    }
                ]
            }
        ];

        // Constraint table rows
        const constraintRows = [
            { range: 'N ≤ 10 – 20', time: 'O(2ⁿ) or O(N!)', paradigms: 'Backtracking, Recursion Trees, Bitmask DP, Permutations / Subsets' },
            { range: 'N ≤ 100 – 500', time: 'O(N³)', paradigms: 'Floyd-Warshall, 3D Dynamic Programming, Matrix Multiplications' },
            { range: 'N ≤ 10³ – 2,000', time: 'O(N²)', paradigms: '2D DP (LCS, Knapsack), Nested Iterations, All-Pairs Comparisons' },
            { range: 'N ≤ 10⁵ – 10⁶', time: 'O(N) or O(N log N)', paradigms: 'Sorting, Two Pointers, Sliding Window, Binary Search, Heaps, Hash Maps, BFS/DFS' },
            { range: 'N ≥ 10⁹', time: 'O(log N) or O(1)', paradigms: 'Binary Search on Answer, Mathematical Formulas, Bit Manipulation' }
        ];

        // Bottleneck table rows
        const bottleneckRows = [
            { bottleneck: 'Repeated linear searches / lookups', technique: 'Hash Map / Hash Set or Frequency Array', gain: 'O(N) → O(1) average lookup' },
            { bottleneck: 'Recalculating overlapping subproblems', technique: 'Dynamic Programming (Memoization / Tabulation)', gain: 'O(2ⁿ) → Polynomial O(N × K)' },
            { bottleneck: 'Searching in ordered / monotonic space', technique: 'Binary Search (or Binary Search on Answer)', gain: 'O(N) → O(log N)' },
            { bottleneck: 'Contiguous subsegments / substrings', technique: 'Sliding Window (Fixed / Variable) & Prefix Sums', gain: 'O(N²) → O(N)' },
            { bottleneck: 'Next greater / smaller element queries', technique: 'Monotonic Stack / Monotonic Queue', gain: 'O(N²) → O(N)' },
            { bottleneck: 'Continuous dynamic extremes (min / max)', technique: 'Priority Queue (Min/Max Heap)', gain: 'O(N log N) → O(N log K)' }
        ];

        const totalItems = stages.reduce((acc, s) => acc + s.items.length, 0);

        return `
        <div class="methodology-checklist-card ${isEmbedded ? 'embedded' : ''}" id="checklistCard-${Utils.escapeHtml(scope)}" data-scope="${Utils.escapeHtml(scope)}">
            <!-- Professional Header -->
            <div class="checklist-header">
                <div class="checklist-header-left">
                    <div class="badge-pill" style="color: var(--color-accent-green); border-color: rgba(17,255,153,0.25); background: rgba(17,255,153,0.05); font-size: 10px; margin-bottom: 6px;">
                        ${Icons.svg('shield-check', {class: 'icon-xs', style: 'color: var(--color-accent-green); margin-right: 4px;'})}
                        <span>PROBLEM-SOLVING METHODOLOGY</span>
                    </div>
                    <h3 class="checklist-title">${Utils.escapeHtml(title)}</h3>
                    <p class="checklist-philosophy">
                        An intuition-first engineering workflow: extract constraints, anchor brute-force, eliminate redundancies, dry-run on paper, and defend complexities.
                    </p>
                </div>

                <div class="checklist-header-actions">
                    <div class="checklist-btn-group">
                        <button type="button" class="btn-ghost btn-sm" data-action="toggle-verbal-mode" data-scope="${Utils.escapeHtml(scope)}" title="Highlight Live Interview Think-Out-Loud protocol">
                            ${Icons.svg('message-square', {class: 'icon-xs'})} <span class="verbal-mode-text">Interview Protocol</span>
                        </button>
                        <button type="button" class="btn-ghost btn-sm" data-action="toggle-all-stages" data-scope="${Utils.escapeHtml(scope)}" title="Expand or collapse all stages">
                            ${Icons.svg('layers', {class: 'icon-xs'})} <span class="toggle-stages-text">Toggle All</span>
                        </button>
                        <button type="button" class="btn-ghost btn-sm" data-action="reset-checklist" data-scope="${Utils.escapeHtml(scope)}" title="Reset checked items">
                            ${Icons.svg('refresh-cw', {class: 'icon-xs'})} Reset
                        </button>
                    </div>
                </div>
            </div>

            <!-- Sleek Minimal Progress Meter -->
            <div class="checklist-progress-card">
                <div class="checklist-progress-top">
                    <div class="flex-row gap-xs" style="align-items: center;">
                        ${Icons.svg('activity', {class: 'icon-xs', style: 'color: var(--color-accent-green);'})}
                        <span class="progress-title">Protocol Completion</span>
                    </div>
                    <div class="flex-row gap-sm" style="align-items: center;">
                        <span class="caption" id="stageCounter-${Utils.escapeHtml(scope)}" style="color: #94a3b8; font-family: var(--font-mono); font-size: 11.5px;">0 of 7 Stages Complete</span>
                        <span class="meta-dot">•</span>
                        <span class="caption" id="itemCounter-${Utils.escapeHtml(scope)}" style="color: #94a3b8; font-family: var(--font-mono); font-size: 11.5px;">0 / ${totalItems} Checked</span>
                        <span class="badge-pill progress-pct-badge" id="percentLabel-${Utils.escapeHtml(scope)}">0%</span>
                    </div>
                </div>
                <div class="progress-bar-track" style="height: 4px; margin-bottom: 0; background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.06);">
                    <div class="progress-bar-fill checklist-fill" id="checklistFill-${Utils.escapeHtml(scope)}" style="width: 0%;"></div>
                </div>
            </div>

            <!-- Stage Accordions -->
            <div class="checklist-stages-list">
                ${stages.map((stage, sIdx) => {
                    const isOpen = defaultOpen || sIdx === 0;
                    return `
                    <div class="checklist-stage-box ${isOpen ? 'open' : ''} ${stage.isBonus ? 'bonus-stage' : ''}" id="stageBox-${Utils.escapeHtml(scope)}-${stage.id}" data-stage-id="${stage.id}">
                        <!-- Stage Accordion Header -->
                        <div class="stage-accordion-header" data-action="toggle-stage" data-target="stageBody-${Utils.escapeHtml(scope)}-${stage.id}">
                            <div class="stage-header-title-group">
                                <span class="stage-index-token">${stage.num}</span>
                                <div style="flex: 1; min-width: 0;">
                                    <div class="stage-title-row">
                                        <span class="stage-heading">${Utils.escapeHtml(stage.title)}</span>
                                        ${stage.badge ? `<span class="tag-pill stage-meta-pill">${Utils.escapeHtml(stage.badge)}</span>` : ''}
                                    </div>
                                    <p class="stage-summary-text">${Utils.escapeHtml(stage.summary)}</p>
                                </div>
                            </div>

                            <div class="stage-header-right">
                                <span class="stage-chip-indicator" id="stageChip-${Utils.escapeHtml(scope)}-${stage.id}">0/${stage.items.length}</span>
                                ${Icons.svg('chevron-down', {class: 'icon-sm stage-chevron'})}
                            </div>
                        </div>

                        <!-- Stage Content Body -->
                        <div class="stage-accordion-body" id="stageBody-${Utils.escapeHtml(scope)}-${stage.id}" style="${isOpen ? '' : 'display: none;'}">
                            <!-- Checklist Items -->
                            <div class="stage-items-list">
                                ${stage.items.map(item => `
                                    <label class="checklist-item-row" for="chk_${Utils.escapeHtml(scope)}_${item.id}">
                                        <input type="checkbox" 
                                            class="methodology-checkbox" 
                                            id="chk_${Utils.escapeHtml(scope)}_${item.id}"
                                            data-scope="${Utils.escapeHtml(scope)}"
                                            data-stage="${stage.id}"
                                            data-item="${item.id}">
                                        <div class="item-text-group">
                                            <div class="item-label">${Utils.escapeHtml(item.label)}</div>
                                            <div class="item-desc">${Utils.escapeHtml(item.desc)}</div>
                                            ${item.tip ? `<div class="item-tip">${Icons.svg('lightbulb', {class: 'icon-xs'})} ${Utils.escapeHtml(item.tip)}</div>` : ''}
                                        </div>
                                    </label>
                                `).join('')}
                            </div>

                            <!-- Embedded Tables -->
                            ${stage.id === 'stage1' ? `
                                <div class="checklist-subtable-box">
                                    <div class="subtable-header">
                                        ${Icons.svg('table', {class: 'icon-xs', style: 'color: var(--color-accent-blue);'})}
                                        <span>Constraint-to-Complexity Decoder</span>
                                    </div>
                                    <div class="table-responsive">
                                        <table class="methodology-data-table">
                                            <thead>
                                                <tr>
                                                    <th>Constraint Range (N)</th>
                                                    <th>Target Complexity</th>
                                                    <th>Applicable Algorithmic Paradigms</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${constraintRows.map(r => `
                                                    <tr>
                                                        <td><code class="code-pill">${Utils.escapeHtml(r.range)}</code></td>
                                                        <td><span class="complexity-pill">${Utils.escapeHtml(r.time)}</span></td>
                                                        <td class="paradigm-cell">${Utils.escapeHtml(r.paradigms)}</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ` : ''}

                            ${stage.id === 'stage3' ? `
                                <div class="checklist-subtable-box">
                                    <div class="subtable-header">
                                        ${Icons.svg('zap', {class: 'icon-xs', style: 'color: var(--color-accent-yellow);'})}
                                        <span>Bottleneck-to-Pattern Optimization Matrix</span>
                                    </div>
                                    <div class="table-responsive">
                                        <table class="methodology-data-table">
                                            <thead>
                                                <tr>
                                                    <th>Identified Bottleneck in Brute Force</th>
                                                    <th>Optimization Technique / Pattern</th>
                                                    <th>Expected Complexity Gain</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${bottleneckRows.map(r => `
                                                    <tr>
                                                        <td class="bottleneck-cell">${Utils.escapeHtml(r.bottleneck)}</td>
                                                        <td><span class="pattern-pill">${Utils.escapeHtml(r.technique)}</span></td>
                                                        <td><span class="gain-pill">${Utils.escapeHtml(r.gain)}</span></td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ` : ''}

                            ${stage.isBonus ? `
                                <div class="interview-protocol-strip">
                                    <div class="protocol-tag">${Icons.svg('message-square', {class: 'icon-xs'})} Candidate Verbal Execution Protocol</div>
                                    <p class="protocol-desc">
                                        Always <strong>think out loud</strong>. Technical interviewers evaluate structured communication, trade-off analysis, and proactive verification just as heavily as raw algorithmic implementation.
                                    </p>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>
        </div>`;
    },

    // ── Standalone Methodology Modal ─────────────────────────────────
    methodologyModal(problemId = '', problemTitle = '') {
        const title = problemTitle ? `Problem Solving Framework · ${problemTitle}` : 'Systematic DSA Problem-Solving Framework';
        return `
        <div class="modal" style="max-width: 860px; width: 95%;">
            <div class="modal-header">
                <h3 class="heading-md flex-row gap-sm" style="align-items: center;">
                    ${Icons.svg('shield-check', {class: 'icon-md', style: 'color: var(--color-accent-green);'})}
                    ${Utils.escapeHtml(title)}
                </h3>
                <button class="btn-icon modal-close" data-action="close-modal" aria-label="Close modal">${Icons.svg('x', {class: 'icon-md'})}</button>
            </div>
            <div style="max-height: 72vh; overflow-y: auto; padding-right: 4px;">
                ${Components.methodologyChecklist(problemId, { embedded: false, defaultOpen: true })}
            </div>
        </div>`;
    },

    // ── Pre-Practice Concept Flashcards Deck ──────────────────────────
    flashcardDeck(flashcards = [], lectureId = '') {
        if (!flashcards || flashcards.length === 0) {
            return Components.emptyState(Icons.svg('brain', {style: 'width: 48px; height: 48px;'}), 'No flashcards available for this lecture yet.');
        }

        const total = flashcards.length;

        return `
        <div class="flashcard-deck-container" id="flashcardDeckContainer-${Utils.escapeHtml(lectureId)}" data-lecture-id="${Utils.escapeHtml(lectureId)}" data-total="${total}">
            <!-- Top Hero Banner & Toolbar -->
            <div class="flashcard-deck-header">
                <div class="flashcard-header-left">
                    <div class="methodology-pill-badge" style="border-color: rgba(59,158,255,0.25); background: rgba(59,158,255,0.06); color: #60a5fa;">
                        ${Icons.svg('brain', {class: 'icon-xs', style: 'color: #60a5fa;'})}
                        <span>PRE-PRACTICE WARM-UP</span>
                    </div>
                    <h3 class="heading-lg" style="margin-top: 4px; margin-bottom: 2px;">Core Concept Flashcards</h3>
                    <p class="caption" style="color: #94a3b8; font-size: 13px;">
                        Warm up your intuition before coding. Review <strong>${total} critical concepts</strong>, high-stress invariants, and common edge cases.
                    </p>
                </div>
                <div class="flashcard-header-right">
                    <button class="btn-ghost btn-sm flex-row gap-xs" data-action="regenerate-flashcards" data-lecture-id="${Utils.escapeHtml(lectureId)}" title="Generate fresh interview-focused cards using AI reasoning">
                        ${Icons.svg('sparkles', {class: 'icon-xs', style: 'color: var(--color-accent-purple);'})} AI Refresh
                    </button>
                    <button class="btn-ghost btn-sm flex-row gap-xs" data-action="shuffle-flashcards" data-lecture-id="${Utils.escapeHtml(lectureId)}" title="Shuffle deck order">
                        ${Icons.svg('sliders', {class: 'icon-xs'})} Shuffle
                    </button>
                    <button class="btn-ghost btn-sm flex-row gap-xs" data-action="toggle-flashcard-view" data-lecture-id="${Utils.escapeHtml(lectureId)}" title="Toggle Card Deck vs List View">
                        ${Icons.svg('layers', {class: 'icon-xs'})} <span class="view-mode-label">Grid View</span>
                    </button>
                </div>
            </div>

            <!-- Progress Strip & Navigation Dots -->
            <div class="flashcard-progress-strip">
                <div class="flashcard-mastery-meta">
                    <div class="flex-row gap-xs" style="align-items: center;">
                        <span class="flashcard-counter-badge" id="fcCurrentNum-${Utils.escapeHtml(lectureId)}">Card 1 of ${total}</span>
                        <span class="meta-dot">•</span>
                        <span class="flashcard-mastery-count" id="fcMasteryCount-${Utils.escapeHtml(lectureId)}">0 / ${total} Mastered</span>
                    </div>
                    <div class="flashcard-keyboard-hint">
                        <span>⌨️ <kbd>Space</kbd> Flip • <kbd>←</kbd> <kbd>→</kbd> Navigate</span>
                    </div>
                </div>

                <div class="flashcard-dots-track" id="fcDotsTrack-${Utils.escapeHtml(lectureId)}">
                    ${flashcards.map((fc, idx) => `
                        <button class="flashcard-dot-btn ${idx === 0 ? 'active' : ''}" data-action="jump-flashcard" data-index="${idx}" title="Jump to Card ${idx + 1}" aria-label="Card ${idx + 1}"></button>
                    `).join('')}
                </div>
            </div>

            <!-- Deck Stage (Focus Mode) -->
            <div class="flashcard-stage-wrapper" id="fcStageWrapper-${Utils.escapeHtml(lectureId)}">
                <div class="flashcard-stage">
                    ${flashcards.map((fc, idx) => {
                        const numStr = String(idx + 1).padStart(2, '0');
                        const cat = fc.category || 'Core Concept';
                        const stress = fc.stress_level || 'Essential';
                        const ts = fc.timestamp || '';
                        const snippet = fc.code_snippet || '';
                        const insight = fc.core_insight || '';

                        return `
                        <div class="flashcard-3d-card ${idx === 0 ? 'active' : ''}" id="fcCard-${Utils.escapeHtml(lectureId)}-${idx}" data-index="${idx}" data-card-id="${Utils.escapeHtml(fc.id || `fc-${idx}`)}">
                            <div class="flashcard-inner" tabindex="0" role="button" aria-label="Flashcard ${idx + 1}. Click to reveal answer." data-action="flip-flashcard">
                                <!-- FRONT FACE: Question & Trap Alert -->
                                <div class="flashcard-face flashcard-front">
                                    <div class="card-face-topbar">
                                        <div class="flex-row gap-xs" style="align-items: center; flex-wrap: wrap;">
                                            <span class="flashcard-category-pill">${Utils.escapeHtml(cat)}</span>
                                            <span class="flashcard-stress-pill ${stress.toLowerCase().replace(/[^a-z]/g, '-')}">${Utils.escapeHtml(stress)}</span>
                                        </div>
                                        <span class="flashcard-index-token">${numStr} / ${String(total).padStart(2, '0')}</span>
                                    </div>

                                    <div class="card-face-body">
                                        <div class="flashcard-question-prompt">
                                            ${Utils.escapeHtml(fc.question)}
                                        </div>
                                    </div>

                                    <div class="card-face-footer">
                                        <div class="reveal-hint-strip">
                                            ${Icons.svg('rotate-cw', {class: 'icon-xs'})}
                                            <span>Click anywhere or press <strong>Space</strong> to reveal answer</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- BACK FACE: Answer, Core Insight & Code Snippet -->
                                <div class="flashcard-face flashcard-back">
                                    <div class="card-face-topbar">
                                        <div class="flex-row gap-xs" style="align-items: center;">
                                            <span class="flashcard-verified-pill">
                                                ${Icons.svg('check-circle-2', {class: 'icon-xs'})} Verified Solution
                                            </span>
                                            ${ts ? `<span class="flashcard-timestamp-pill">${Icons.svg('clock', {class: 'icon-xs'})} ${Utils.escapeHtml(ts)}</span>` : ''}
                                        </div>
                                        <span class="flashcard-index-token">${numStr} / ${String(total).padStart(2, '0')}</span>
                                    </div>

                                    <div class="card-face-body">
                                        <div class="flashcard-answer-text">
                                            ${Utils.escapeHtml(fc.answer).replace(/\n/g, '<br>')}
                                        </div>

                                        ${insight ? `
                                        <div class="flashcard-insight-box">
                                            <div class="insight-label">${Icons.svg('sparkles', {class: 'icon-xs', style: 'color: #fbbf24;'})} Key Takeaway</div>
                                            <div class="insight-text">${Utils.escapeHtml(insight)}</div>
                                        </div>` : ''}

                                        ${snippet ? `
                                        <div class="flashcard-code-box">
                                            <pre><code>${Utils.escapeHtml(snippet)}</code></pre>
                                        </div>` : ''}
                                    </div>

                                    <div class="card-face-footer card-back-footer" onclick="event.stopPropagation();">
                                        <div class="flashcard-rating-group">
                                            <span class="rating-label">Mastery self-check:</span>
                                            <div class="flex-row gap-xs">
                                                <button type="button" class="btn-ghost btn-xs rating-btn rating-review" data-action="rate-flashcard" data-rating="review" data-index="${idx}" title="Need to review this concept again">
                                                    ${Icons.svg('rotate-cw', {class: 'icon-xs'})} Review Again
                                                </button>
                                                <button type="button" class="btn-ghost btn-xs rating-btn rating-mastered" data-action="rate-flashcard" data-rating="mastered" data-index="${idx}" title="I know this concept solidly">
                                                    ${Icons.svg('check', {class: 'icon-xs'})} Got It!
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>

                <!-- Deck Controls -->
                <div class="flashcard-controls-bar">
                    <button class="btn-ghost btn-sm flex-row gap-xs" data-action="prev-flashcard" data-lecture-id="${Utils.escapeHtml(lectureId)}" id="fcPrevBtn-${Utils.escapeHtml(lectureId)}">
                        ${Icons.svg('arrow-left', {class: 'icon-xs'})} Previous
                    </button>
                    
                    <button class="btn-primary btn-sm flex-row gap-xs" data-action="flip-current-flashcard" data-lecture-id="${Utils.escapeHtml(lectureId)}">
                        ${Icons.svg('rotate-cw', {class: 'icon-xs'})} Flip Card
                    </button>

                    <button class="btn-ghost btn-sm flex-row gap-xs" data-action="next-flashcard" data-lecture-id="${Utils.escapeHtml(lectureId)}" id="fcNextBtn-${Utils.escapeHtml(lectureId)}">
                        Next ${Icons.svg('arrow-right', {class: 'icon-xs'})}
                    </button>
                </div>
            </div>

            <!-- Grid / List Mode Container (Hidden by default) -->
            <div class="flashcard-grid-view" id="fcGridView-${Utils.escapeHtml(lectureId)}" style="display: none;">
                <div class="flex-col gap-md">
                    ${flashcards.map((fc, idx) => `
                        <div class="flashcard-list-item glass-card" id="fcListItem-${Utils.escapeHtml(lectureId)}-${idx}">
                            <div class="flex-between" style="cursor: pointer;" data-action="toggle-list-card" data-target="fcListBody-${Utils.escapeHtml(lectureId)}-${idx}">
                                <div class="flex-row gap-sm" style="align-items: center;">
                                    <span class="flashcard-index-token">${String(idx + 1).padStart(2, '0')}</span>
                                    <span class="flashcard-category-pill">${Utils.escapeHtml(fc.category || 'Core Concept')}</span>
                                    <strong class="body-sm">${Utils.escapeHtml(fc.question)}</strong>
                                </div>
                                <div class="flex-row gap-xs">
                                    <span class="badge-pill" style="font-size: 11px;">Click to Reveal</span>
                                    ${Icons.svg('chevron-down', {class: 'icon-xs'})}
                                </div>
                            </div>
                            <div class="flashcard-list-body" id="fcListBody-${Utils.escapeHtml(lectureId)}-${idx}" style="display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06);">
                                <div class="body-sm" style="color: #cbd5e1; line-height: 1.6; margin-bottom: 8px;">
                                    ${Utils.escapeHtml(fc.answer).replace(/\n/g, '<br>')}
                                </div>
                                ${fc.core_insight ? `<div class="flashcard-insight-box"><div class="insight-label">${Icons.svg('sparkles', {class: 'icon-xs'})} Key Takeaway</div><div>${Utils.escapeHtml(fc.core_insight)}</div></div>` : ''}
                                ${fc.code_snippet ? `<div class="flashcard-code-box"><pre><code>${Utils.escapeHtml(fc.code_snippet)}</code></pre></div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>`;
    },

    // ── Standalone Flashcard Modal ────────────────────────────────────
    flashcardModal(flashcards = [], lectureTitle = '', lectureId = '') {
        return `
        <div class="modal" style="max-width: 820px; width: 95%;">
            <div class="modal-header">
                <h3 class="heading-md flex-row gap-sm" style="align-items: center;">
                    ${Icons.svg('brain', {class: 'icon-md', style: 'color: #60a5fa;'})}
                    <span>Pre-Practice Warm-up · ${Utils.escapeHtml(lectureTitle)}</span>
                </h3>
                <button class="btn-icon modal-close" data-action="close-modal" aria-label="Close dialog">${Icons.svg('x', {class: 'icon-md'})}</button>
            </div>
            <div style="max-height: 75vh; overflow-y: auto; padding-right: 4px;">
                ${Components.flashcardDeck(flashcards, lectureId)}
            </div>
        </div>`;
    }
};

window.Components = Components;


