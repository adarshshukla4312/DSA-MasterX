window.HomePage = {
    async render(container) {
        this.container = container;
        
        // Initial Loading state
        container.innerHTML = `
            ${Components.heroBanner('GritX', 'An AI-powered pipeline that transforms raw DSA lecture videos into a structured problem database, complete with spaced repetition review and auto-generated practice sheets.', 'System Active')}
            <div class="grid-4 gap-md stagger-in" style="margin: 2rem 0;">
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
            </div>
            ${Components.sectionHeader('Workflow Architecture', '', 'layers')}
            <div class="grid-4 gap-md stagger-in">
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
                ${Components.skeletonCard()}
            </div>
        `;
        
        try {
            const stats = await API.stats();
            this.renderContent(stats || {});
        } catch (error) {
            console.error('Failed to load stats', error);
            this.renderContent({});
        }
    },

    renderContent(stats) {
        const html = `
            ${Components.heroBanner('GritX', 'An AI-powered pipeline that transforms raw DSA lecture videos into a structured problem database, complete with spaced repetition review and auto-generated practice sheets.', 'System Active')}
            
            <div class="grid-4 gap-md stagger-in" style="margin: 2rem 0;">
                ${Components.statCard(stats.total_lectures || 0, 'Total Lectures', '#/library')}
                ${Components.statCard(stats.total_problems || 0, 'Problem Database', '#/problems')}
                ${Components.statCard(stats.solved_count ?? stats.solved_problems ?? 0, 'Problems Solved', '#/practice')}
                ${Components.statCard(stats.processed_count ?? stats.identified_lectures ?? 0, 'Identified Lectures', '#/library')}
            </div>

            ${Components.sectionHeader('Workflow Architecture', '', 'layers')}
            
            <div class="grid-4 gap-md stagger-in" style="margin-bottom: 2rem;">
                <a href="#/library" style="text-decoration: none; color: inherit; display: block;">
                    ${Components.glassCard(`
                        ${Icons.svg('refresh-cw', {class: 'icon-lg', style: 'margin-bottom: 12px; color: var(--color-accent-blue);'})}
                        <h3 class="heading-sm" style="margin-bottom: 8px;">1. Scan & Process</h3>
                        <p class="body-sm" style="color: var(--color-charcoal);">Automatically index lecture folders, extract audio, and transcribe using Whisper.</p>
                    `)}
                </a>
                <a href="#/problems" style="text-decoration: none; color: inherit; display: block;">
                    ${Components.glassCard(`
                        ${Icons.svg('code-2', {class: 'icon-lg', style: 'margin-bottom: 12px; color: var(--color-accent-green);'})}
                        <h3 class="heading-sm" style="margin-bottom: 8px;">2. Identified Code</h3>
                        <p class="body-sm" style="color: var(--color-charcoal);">LLMs identify coding problems, core tricks, and extract code from transcriptions.</p>
                    `)}
                </a>
                <a href="#/practice" style="text-decoration: none; color: inherit; display: block;">
                    ${Components.glassCard(`
                        ${Icons.svg('file-check-2', {class: 'icon-lg', style: 'margin-bottom: 12px; color: var(--color-accent-red);'})}
                        <h3 class="heading-sm" style="margin-bottom: 8px;">3. Practice Sheets</h3>
                        <p class="body-sm" style="color: var(--color-charcoal);">Generates interactive multiple-choice questions and conceptual ladder steps.</p>
                    `)}
                </a>
                <a href="#/dashboard" style="text-decoration: none; color: inherit; display: block;">
                    ${Components.glassCard(`
                        ${Icons.svg('repeat', {class: 'icon-lg', style: 'margin-bottom: 12px; color: var(--color-accent-orange);'})}
                        <h3 class="heading-sm" style="margin-bottom: 8px;">4. SM-2 Spaced Review</h3>
                        <p class="body-sm" style="color: var(--color-charcoal);">Review problem patterns on an optimized schedule to maximize retention.</p>
                    `)}
                </a>
            </div>
        `;
        
        this.container.innerHTML = html;
    },
    
    destroy() {
        this.container = null;
    }
};
