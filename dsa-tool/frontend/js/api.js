// GritX — API Client
const API = {
    BASE: '/api',
    
    async _fetch(path, options = {}) {
        try {
            const url = path.startsWith('http') ? path : `${this.BASE}${path}`;
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                let errorMsg = response.statusText;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMsg = errorData.error;
                    } else if (errorData && errorData.detail) {
                        errorMsg = errorData.detail;
                    }
                } catch(e) {
                    // Could not parse JSON error response
                }
                throw new Error(errorMsg || `HTTP error ${response.status}`);
            }
            
            // Check if response is empty
            const text = await response.text();
            return text ? JSON.parse(text) : {};
        } catch (error) {
            console.error(`API Error on ${path}:`, error);
            throw error;
        }
    },
    
    async get(path) {
        return this._fetch(path, { method: 'GET' });
    },
    
    async post(path, body = {}) {
        return this._fetch(path, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },
    
    // Lectures
    lectures: {
        list: () => API.get('/lectures'),
        get: (id) => API.get(`/lectures/${encodeURIComponent(id)}`),
        scan: () => API.post('/lectures/scan'),
        process: (id, skipTranscription = false) => API.post(`/lectures/${encodeURIComponent(id)}/process`, { skip_transcription: skipTranscription }),
        processAll: () => API.post('/lectures/process-all'),
        jobStatus: (id) => API.get(`/lectures/${encodeURIComponent(id)}/job`),
        cancel: (id) => API.post(`/lectures/${encodeURIComponent(id)}/cancel`),
        matches: (id) => API.get(`/lectures/${encodeURIComponent(id)}/matches`),
        practice: (id) => API.get(`/lectures/${encodeURIComponent(id)}/practice`),
        challenge: (id) => API.post(`/lectures/${encodeURIComponent(id)}/challenge`),
        flashcards: (id) => API.get(`/lectures/${encodeURIComponent(id)}/flashcards`),
        generateFlashcards: (id) => API.post(`/lectures/${encodeURIComponent(id)}/flashcards/generate`),
    },
    
    // Problems
    problems: {
        list: () => API.get('/problems'),
        solved: () => API.get('/problems/solved'),
    },
    
    // Attempts
    attempts: {
        log: (data) => API.post('/attempts', data),
        list: (problemId = null) => API.get(problemId ? `/attempts?problem_id=${encodeURIComponent(problemId)}` : '/attempts'),
    },
    
    // Revision
    revision: {
        due: () => API.get('/revision/due'),
        stats: () => API.get('/revision/stats'),
    },
    
    // Settings
    settings: {
        getLectureDir: () => API.get('/settings/lecture-dir'),
        setLectureDir: (lectureDir) => API.post('/settings/lecture-dir', { lecture_dir: lectureDir }),
        validateDir: (path) => API.get(`/settings/validate-dir?path=${encodeURIComponent(path)}`),
        browseFolder: () => API.post('/settings/browse-folder'),
    },

    
    // Dashboard
    stats: () => API.get('/stats'),
    hardware: () => API.get('/hardware'),
    pipelineHash: () => API.get('/pipeline-hash'),
    logs: (lines = 40) => API.get(`/logs?lines=${lines}`),
};

