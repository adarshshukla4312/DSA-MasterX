const Utils = {
    // Format file size: bytes to human readable
    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        if (!bytes) return 'Unknown';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },
    
    // Format date: ISO string to 'Aug 13, 2026'
    formatDate(isoString) {
        if (!isoString) return 'Never';
        const date = new Date(isoString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    },
    
    // Format relative time: '2 hours ago', 'yesterday'
    formatRelativeTime(isoString) {
        if (!isoString) return 'Never';
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.round(diffMs / 1000);
        const diffMins = Math.round(diffSecs / 60);
        const diffHrs = Math.round(diffMins / 60);
        const diffDays = Math.round(diffHrs / 24);
        
        if (diffSecs < 60) return 'just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHrs < 24) return `${diffHrs} hour${diffHrs > 1 ? 's' : ''} ago`;
        if (diffDays === 1) return 'yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return this.formatDate(isoString);
    },
    
    // Debounce function for search inputs
    debounce(fn, delay = 300) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    },
    
    // Format mathematical & complexity notations with superscripts and subscripts (e.g. O(n^2) -> O(n²), 2^n -> 2ⁿ, A_i -> Aᵢ)
    formatMath(str) {
        if (!str) return '';
        const SUPERSCRIPTS = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
            'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ',
            'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ',
            'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
            'A': 'ᴬ', 'B': 'ᴮ', 'D': 'ᴰ', 'E': 'ᴱ', 'G': 'ᴳ', 'H': 'ᴴ', 'I': 'ᴵ', 'J': 'ᴶ', 'K': 'ᴷ', 'L': 'ᴸ',
            'M': 'ᴹ', 'N': 'ᴺ', 'O': 'ᴼ', 'P': 'ᴾ', 'R': 'ᴿ', 'T': 'ᵀ', 'U': 'ᵁ', 'V': 'ⱽ', 'W': 'ᵂ'
        };

        const SUBSCRIPTS = {
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
            '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
            'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
            'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ'
        };

        let s = String(str).replace(/\$([^$]+)\$/g, '$1');

        // 1. Explicit braces/parens: ^{...} or ^(...)
        s = s.replace(/\^\{([a-zA-Z0-9+\-]+)\}/g, (m, g) => g.split('').map(c => SUPERSCRIPTS[c] || c).join(''));
        s = s.replace(/\^\(([a-zA-Z0-9+\-]+)\)/g, (m, g) => g.split('').map(c => SUPERSCRIPTS[c] || c).join(''));

        // 2. Standard token exponents: ^2, ^3, ^n, ^k, ^N, ^10
        s = s.replace(/\^([a-zA-Z0-9]+)/g, (m, g) => g.split('').map(c => SUPERSCRIPTS[c] || c).join(''));

        // 3. Explicit subscripts: _{...} or _(...)
        s = s.replace(/_\{([a-zA-Z0-9+\-]+)\}/g, (m, g) => g.split('').map(c => SUBSCRIPTS[c] || c).join(''));
        s = s.replace(/_\(([a-zA-Z0-9+\-]+)\)/g, (m, g) => g.split('').map(c => SUBSCRIPTS[c] || c).join(''));

        // 4. Single character subscripts: _i, _j, _k, _0, _1, _n
        s = s.replace(/_([a-zA-Z0-9])/g, (m, g) => SUBSCRIPTS[g] || `_${g}`);

        // 5. Multiplication symbol in Big-O notation e.g. O(N * M) -> O(N · M)
        s = s.replace(/O\(([^)]+)\)/g, (m, inner) => `O(${inner.replace(/\s*\*\s*/g, ' · ')})`);

        return s;
    },

    // Escape HTML to prevent XSS and format math superscripts/subscripts
    escapeHtml(str) {
        if (str === null || str === undefined) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return this.formatMath(div.innerHTML);
    },

    // Syntax highlight Java code in authentic IntelliJ IDEA Darcula/New UI color scheme
    highlightJava(code) {
        if (!code) return '';

        const KEYWORDS = new Set([
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const',
            'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float',
            'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native',
            'new', 'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp',
            'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'void',
            'volatile', 'while', 'null', 'true', 'false', 'record', 'sealed', 'permits', 'var', 'yield'
        ]);

        const BUILTIN_TYPES = new Set([
            'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Character', 'Byte', 'Short',
            'List', 'ArrayList', 'LinkedList', 'Set', 'HashSet', 'TreeSet', 'LinkedHashSet',
            'Map', 'HashMap', 'TreeMap', 'LinkedHashMap', 'Queue', 'Deque', 'ArrayDeque', 'PriorityQueue',
            'Stack', 'Vector', 'Arrays', 'Collections', 'Math', 'StringBuilder', 'StringBuffer',
            'Scanner', 'System', 'Object', 'Override', 'Deprecated', 'SuppressWarnings',
            'TreeNode', 'ListNode', 'Node', 'Pair', 'Solution', 'leet78'
        ]);

        const lines = String(code).split('\n');

        return lines.map((line, idx) => {
            let processed = '';
            let i = 0;
            const len = line.length;

            while (i < len) {
                // Line comment
                if (line.slice(i, i + 2) === '//') {
                    const comment = line.slice(i);
                    processed += `<span class="ij-comment">${this.escapeHtml(comment)}</span>`;
                    break;
                }

                // String literal
                if (line[i] === '"') {
                    let j = i + 1;
                    while (j < len && (line[j] !== '"' || line[j - 1] === '\\')) j++;
                    const str = line.slice(i, j + 1);
                    processed += `<span class="ij-string">${this.escapeHtml(str)}</span>`;
                    i = j + 1;
                    continue;
                }

                // Char literal
                if (line[i] === "'") {
                    let j = i + 1;
                    while (j < len && (line[j] !== "'" || line[j - 1] === '\\')) j++;
                    const ch = line.slice(i, j + 1);
                    processed += `<span class="ij-string">${this.escapeHtml(ch)}</span>`;
                    i = j + 1;
                    continue;
                }

                // Annotation (@Override, @...)
                if (line[i] === '@' && /[a-zA-Z]/.test(line[i + 1] || '')) {
                    let j = i + 1;
                    while (j < len && /[a-zA-Z0-9_]/.test(line[j])) j++;
                    const ann = line.slice(i, j);
                    processed += `<span class="ij-annotation">${this.escapeHtml(ann)}</span>`;
                    i = j;
                    continue;
                }

                // Numbers (hex, binary, float, int)
                if (/\d/.test(line[i]) && (i === 0 || !/[a-zA-Z0-9_$]/.test(line[i - 1]))) {
                    let j = i;
                    if (line[j] === '0' && (line[j + 1] === 'x' || line[j + 1] === 'X')) {
                        j += 2;
                        while (j < len && /[0-9a-fA-F_]/.test(line[j])) j++;
                    } else if (line[j] === '0' && (line[j + 1] === 'b' || line[j + 1] === 'B')) {
                        j += 2;
                        while (j < len && /[01_]/.test(line[j])) j++;
                    } else {
                        while (j < len && /[0-9._fFdDlL]/.test(line[j])) j++;
                    }
                    const num = line.slice(i, j);
                    processed += `<span class="ij-number">${this.escapeHtml(num)}</span>`;
                    i = j;
                    continue;
                }

                // Identifiers & Keywords
                if (/[a-zA-Z_$]/.test(line[i])) {
                    let j = i;
                    while (j < len && /[a-zA-Z0-9_$]/.test(line[j])) j++;
                    const word = line.slice(i, j);

                    // Check if property like .length or .size
                    const isProperty = i > 0 && line[i - 1] === '.' && (word === 'length' || word === 'size');

                    // Check if followed by opening paren '(' (Method call or definition)
                    let nextNonSpace = j;
                    while (nextNonSpace < len && /\s/.test(line[nextNonSpace])) nextNonSpace++;
                    const isMethod = line[nextNonSpace] === '(' && !KEYWORDS.has(word);

                    if (isProperty) {
                        processed += `<span class="ij-property">${this.escapeHtml(word)}</span>`;
                    } else if (KEYWORDS.has(word)) {
                        processed += `<span class="ij-keyword">${this.escapeHtml(word)}</span>`;
                    } else if (BUILTIN_TYPES.has(word) || /^[A-Z][a-zA-Z0-9_$]*$/.test(word)) {
                        processed += `<span class="ij-type">${this.escapeHtml(word)}</span>`;
                    } else if (isMethod) {
                        processed += `<span class="ij-method">${this.escapeHtml(word)}</span>`;
                    } else {
                        processed += `<span class="ij-identifier">${this.escapeHtml(word)}</span>`;
                    }

                    i = j;
                    continue;
                }

                // Operators & Punctuation
                processed += this.escapeHtml(line[i]);
                i++;
            }

            const lineNum = idx + 1;
            return `<div class="ij-line"><span class="ij-gutter" aria-hidden="true">${lineNum}</span><span class="ij-code-content">${processed || '&nbsp;'}</span></div>`;
        }).join('');
    },
    
    // Generate Google search URL for a problem
    googleSearchUrl(title, platform = 'LeetCode') {
        if (!title) return '#';
        const query = encodeURIComponent(`${title} ${platform}`);
        return `https://www.google.com/search?q=${query}`;
    },
    
    // Truncate text with ellipsis
    truncate(str, maxLen = 80) {
        if (!str) return '';
        if (str.length <= maxLen) return str;
        return str.slice(0, maxLen) + '...';
    },
    
    // Simple template literal helper for creating elements
    createElement(html) {
        const template = document.createElement('template');
        template.innerHTML = html.trim();
        return template.content.firstChild;
    },
    
    // Batch DOM updates with document fragment
    createFragment(elements) {
        const fragment = document.createDocumentFragment();
        elements.forEach(el => {
            if (el) fragment.appendChild(el);
        });
        return fragment;
    },
    
    // Difficulty to CSS class
    diffClass(difficulty) {
        const diff = (difficulty || 'medium').toLowerCase();
        if (diff === 'hard') return 'diff-hard';
        if (diff === 'easy') return 'diff-easy';
        return 'diff-medium';
    },
    
    // Status to display text
    statusLabel(status) {
        const s = (status || '').toLowerCase();
        if (s === 'completed' || s === 'complete' || s === 'identified' || s === 'matched' || s === 'extracted') return 'Complete';
        if (s === 'new') return 'New';
        if (s === 'processing' || s === 'starting') return 'Processing';
        if (s === 'transcribed') return 'Incomplete';
        if (s === 'failed') return 'Failed';
        return status || 'New';
    },

    // Button loading helper maintaining layout dimensions
    setButtonLoading(btn, isLoading, loadingText = '') {
        if (!btn) return;
        if (isLoading) {
            btn.dataset.originalHtml = btn.innerHTML;
            btn.classList.add('btn-loading');
            btn.disabled = true;
            btn.setAttribute('aria-busy', 'true');
            if (loadingText) btn.dataset.loadingText = loadingText;
        } else {
            btn.classList.remove('btn-loading');
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            if (btn.dataset.originalHtml) {
                btn.innerHTML = btn.dataset.originalHtml;
                delete btn.dataset.originalHtml;
            }
        }
    },

    // Clipboard copy with feedback
    async copyToClipboard(text, btnElement = null) {
        try {
            await navigator.clipboard.writeText(text);
            if (btnElement) {
                const originalHtml = btnElement.innerHTML;
                btnElement.innerHTML = `${Icons.svg('check', {class: 'icon-sm'})} Copied!`;
                btnElement.classList.add('copied');
                setTimeout(() => {
                    btnElement.innerHTML = originalHtml;
                    btnElement.classList.remove('copied');
                }, 2000);
            }
            return true;
        } catch (err) {
            console.error('Failed to copy to clipboard:', err);
            return false;
        }
    },

    // Natural numeric comparator for lecture lists (1 -> 2 -> 3 ... 10 -> 11 -> 20 -> 45)
    compareLectures(a, b) {
        if (!a && !b) return 0;
        if (!a) return 1;
        if (!b) return -1;
        const getNum = (item) => {
            if (item.num !== undefined && item.num !== null && String(item.num).trim() !== '' && !isNaN(parseInt(item.num, 10))) {
                return parseInt(item.num, 10);
            }
            const str = item.filename || item.id || item.title || '';
            const match = str.match(/^(\d+)/);
            if (match) return parseInt(match[1], 10);
            const matchL = str.match(/^l(\d+)/i);
            if (matchL) return parseInt(matchL[1], 10);
            return 999999;
        };
        const numA = getNum(a);
        const numB = getNum(b);
        if (numA !== numB) return numA - numB;
        return (a.title || a.filename || '').localeCompare(b.title || b.filename || '', undefined, { numeric: true, sensitivity: 'base' });
    },

    // Comprehensive multi-field lecture search matcher
    matchLecture(lecture, rawQuery) {
        if (!rawQuery || !rawQuery.trim()) return true;
        if (!lecture) return false;

        const query = rawQuery.toLowerCase().trim();
        
        // 1. Direct Lecture Number Prefix/Shorthand Check (e.g. "l45", "l 45", "lec 45", "lecture 45", "#45", "45")
        const numStr = lecture.num ? String(lecture.num).trim().toLowerCase() : '';
        const idStr = (lecture.id || '').toLowerCase();
        const filenameStr = (lecture.filename || '').toLowerCase();

        const lecPattern = /^(?:l|lec|lecture|#)?\s*(\d+)(.*)$/i;
        const match = query.match(lecPattern);
        if (match) {
            const queryNum = match[1];
            const remaining = (match[2] || '').trim();

            const isNumMatch = numStr === queryNum || 
                               idStr.startsWith(`${queryNum}-`) || 
                               idStr.startsWith(`${queryNum}_`) || 
                               filenameStr.startsWith(`${queryNum}.`) ||
                               filenameStr.startsWith(`${queryNum} `) ||
                               filenameStr.startsWith(`${queryNum}-`);

            if (isNumMatch) {
                if (!remaining) return true; // Direct "L45" or "45"
                const remainingTokens = remaining.replace(/[^a-z0-9]/gi, ' ').split(/\s+/).filter(Boolean);
                const fullText = this.getLectureSearchBlob(lecture);
                if (remainingTokens.every(t => fullText.includes(t))) return true;
            }
        }

        // 2. Build full searchable blob
        const searchBlob = this.getLectureSearchBlob(lecture);

        // 3. Exact Substring Match
        if (searchBlob.includes(query)) return true;

        // 4. Normalized Punctuation Substring Match (e.g. "arrays 1" matches "arrays - 1" or "arrays _ 1")
        const cleanBlob = searchBlob.replace(/[^a-z0-9]/g, ' ');
        const cleanQuery = query.replace(/[^a-z0-9]/g, ' ').trim();
        if (cleanQuery && cleanBlob.includes(cleanQuery)) return true;

        // 5. Multi-token AND matching (all query words must match somewhere in the lecture blob)
        const tokens = cleanQuery.split(/\s+/).filter(Boolean);
        if (tokens.length > 0) {
            const allTokensMatch = tokens.every(token => {
                const tokLecMatch = token.match(/^l(\d+)$/);
                if (tokLecMatch) {
                    const tNum = tokLecMatch[1];
                    return cleanBlob.includes(token) || cleanBlob.includes(tNum) || numStr === tNum;
                }
                return cleanBlob.includes(token);
            });
            if (allTokensMatch) return true;
        }

        return false;
    },

    getLectureSearchBlob(lecture) {
        if (!lecture) return '';
        const parts = [];

        // Number variants
        if (lecture.num) {
            const n = String(lecture.num).trim();
            parts.push(n, `l${n}`, `l ${n}`, `lec ${n}`, `lecture ${n}`, `#${n}`, `l-${n}`, `l_${n}`);
        }

        // Titles, Filename, ID, Meta
        if (lecture.title) parts.push(lecture.title);
        if (lecture.filename) parts.push(lecture.filename);
        if (lecture.id) parts.push(lecture.id, lecture.id.replace(/[-_]/g, ' '));
        if (lecture.difficulty) parts.push(lecture.difficulty);
        if (lecture.status) parts.push(lecture.status);

        // Topics
        if (Array.isArray(lecture.topics)) {
            parts.push(...lecture.topics);
        }

        // Techniques
        if (Array.isArray(lecture.techniques)) {
            parts.push(...lecture.techniques);
        }

        // Problems Discussed & Matches
        if (Array.isArray(lecture.problems_discussed)) {
            lecture.problems_discussed.forEach(p => {
                if (p.title) parts.push(p.title);
                if (p.name) parts.push(p.name);
                if (p.matched_problem_id) parts.push(p.matched_problem_id);
                if (p.core_trick) parts.push(p.core_trick);
                if (p.approach) parts.push(p.approach);
            });
        }

        return parts.join(' ').toLowerCase();
    },

    // Cleanly parse and format lecture numbers, modules, and topic names
    parseLectureTitle(rawTitle, rawNum, filename = '', id = '') {
        let num = rawNum;
        if (num === undefined || num === null || String(num).trim() === '' || isNaN(parseInt(num, 10))) {
            const match = (filename || id || rawTitle || '').match(/^(\d+)/);
            if (match) num = parseInt(match[1], 10);
            else {
                const matchL = (filename || id || rawTitle || '').match(/^l(\d+)/i);
                if (matchL) num = parseInt(matchL[1], 10);
            }
        } else {
            num = parseInt(num, 10);
        }

        let title = (rawTitle || '').trim();
        // Remove leading numeric prefixes like "22. ", "22 - ", "22_", "L22: "
        title = title.replace(/^(?:l\d+[\s:.\-_]+|\d+[\s:.\-_]+)+/i, '').trim();

        let moduleName = '';
        let topic = title;

        if (title.includes(' _ ')) {
            const parts = title.split(' _ ');
            moduleName = parts[0].trim();
            topic = parts.slice(1).join(' · ').trim();
        } else if (title.includes(' — ')) {
            const parts = title.split(' — ');
            moduleName = parts[0].trim();
            topic = parts.slice(1).join(' · ').trim();
        } else if (title.includes(' - ') && (title.startsWith('Intermediate DSA') || title.startsWith('Advanced DSA') || title.startsWith('Beginner') || title.startsWith('Beginner Java'))) {
            const parts = title.split(' - ');
            moduleName = parts[0].trim();
            topic = parts.slice(1).join(' · ').trim();
        }

        // Clean up remaining underscores and double spaces
        topic = topic.replace(/_/g, ' ').replace(/\s{2,}/g, ' ').trim();
        moduleName = moduleName.replace(/_/g, ' ').replace(/\s{2,}/g, ' ').trim();

        if (!topic && moduleName) {
            topic = moduleName;
            moduleName = '';
        }

        return {
            num: num || null,
            numStr: num ? `L${num}` : '',
            module: moduleName,
            topic: topic || title || 'Untitled Lecture',
            fullTitle: moduleName ? `${moduleName} · ${topic}` : (topic || 'Untitled Lecture')
        };
    }
};

window.Utils = Utils;
