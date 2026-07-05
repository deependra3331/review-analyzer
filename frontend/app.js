const API_BASE = 'http://localhost:8000'; // Update if deployed

// Elements
const elements = {
    themesList: document.getElementById('themesList'),
    needsList: document.getElementById('needsList'),
    jtbdList: document.getElementById('jtbdList'),
    segmentList: document.getElementById('segmentList'),
    globalInsights: document.getElementById('globalInsights'),
    globalInsightsGrid: document.getElementById('globalInsightsGrid'),
    runBtn: document.getElementById('runBtn'),
    statusIndicator: document.getElementById('statusIndicator'),
    runSelect: document.getElementById('runSelect'),
    drawerOverlay: document.getElementById('drawerOverlay'),
    evidenceDrawer: document.getElementById('evidenceDrawer'),
    closeDrawerBtn: document.getElementById('closeDrawerBtn'),
    drawerTitle: document.getElementById('drawerTitle'),
    drawerContent: document.getElementById('drawerContent'),
};

// State
let currentRunData = null;
const patterns = ['pattern-dots', 'pattern-lines', 'pattern-cross'];

// Init
async function init() {
    setupEventListeners();
    await fetchRuns();
}

function setupEventListeners() {
    elements.runBtn.addEventListener('click', triggerRun);
    elements.runSelect.addEventListener('change', (e) => loadRun(e.target.value));
    elements.closeDrawerBtn.addEventListener('click', closeDrawer);
    elements.drawerOverlay.addEventListener('click', closeDrawer);
}

async function fetchRuns() {
    try {
        const res = await fetch(`${API_BASE}/runs`);
        const runs = await res.json();
        
        elements.runSelect.innerHTML = '';
        if (runs.length === 0) {
            elements.runSelect.innerHTML = '<option>No runs available</option>';
            return;
        }

        runs.forEach((run, idx) => {
            const opt = document.createElement('option');
            opt.value = run.id;
            opt.textContent = `Run #${run.id} - ${new Date(run.date_run).toLocaleDateString()}`;
            elements.runSelect.appendChild(opt);
        });

        loadRun(runs[0].id);
    } catch (err) {
        console.error('Failed to fetch runs', err);
    }
}

async function loadRun(runId) {
    if (!runId || runId === 'No runs available') return;
    try {
        const res = await fetch(`${API_BASE}/runs/${runId}`);
        const run = await res.json();
        currentRunData = run;
        renderDashboard(run);
    } catch (err) {
        console.error('Failed to load run', err);
    }
}

async function triggerRun() {
    elements.runBtn.disabled = true;
    elements.runBtn.textContent = 'Running...';
    elements.runBtn.classList.add('opacity-50');
    
    try {
        await fetch(`${API_BASE}/runs`, { method: 'POST' });
        // Simulating polling
        setTimeout(async () => {
            await fetchRuns();
            elements.runBtn.disabled = false;
            elements.runBtn.textContent = 'Run Analysis Pipeline';
            elements.runBtn.classList.remove('opacity-50');
        }, 3000);
    } catch (err) {
        console.error('Failed to trigger run', err);
        elements.runBtn.disabled = false;
        elements.runBtn.textContent = 'Run Analysis Pipeline';
        elements.runBtn.classList.remove('opacity-50');
    }
}

function renderDashboard(runData) {
    if (!runData || !runData.clusters) return;

    if (runData.global_insight) {
        elements.globalInsights.classList.remove('hidden');
        const gi = runData.global_insight;
        elements.globalInsightsGrid.innerHTML = `
            <div class="glass p-4 rounded-xl hover-lift">
                <h3 class="text-xs font-bold text-spotify uppercase tracking-wider mb-2">Discovery Struggle</h3>
                <p class="text-sm text-textSecondary">${gi.struggle_reason || 'N/A'}</p>
            </div>
            <div class="glass p-4 rounded-xl hover-lift">
                <h3 class="text-xs font-bold text-spotify uppercase tracking-wider mb-2">Common Frustrations</h3>
                <p class="text-sm text-textSecondary">${gi.common_frustrations || 'N/A'}</p>
            </div>
            <div class="glass p-4 rounded-xl hover-lift">
                <h3 class="text-xs font-bold text-spotify uppercase tracking-wider mb-2">Listening Behaviors</h3>
                <p class="text-sm text-textSecondary">${gi.listening_behaviors || 'N/A'}</p>
            </div>
            <div class="glass p-4 rounded-xl hover-lift">
                <h3 class="text-xs font-bold text-spotify uppercase tracking-wider mb-2">Repeat Causes</h3>
                <p class="text-sm text-textSecondary">${gi.repeat_causes || 'N/A'}</p>
            </div>
            <div class="glass p-4 rounded-xl hover-lift">
                <h3 class="text-xs font-bold text-spotify uppercase tracking-wider mb-2">Segment Challenges</h3>
                <p class="text-sm text-textSecondary">${gi.segment_challenges || 'N/A'}</p>
            </div>
            <div class="glass p-4 rounded-xl hover-lift">
                <h3 class="text-xs font-bold text-spotify uppercase tracking-wider mb-2">Unmet Needs</h3>
                <p class="text-sm text-textSecondary">${gi.unmet_needs_summary || 'N/A'}</p>
            </div>
        `;
    } else {
        elements.globalInsights.classList.add('hidden');
    }

    if (runData.clusters.length === 0) {
        elements.themesList.innerHTML = '<div class="text-textSecondary">No themes found for this run.</div>';
        elements.needsList.innerHTML = '';
        elements.jtbdList.innerHTML = '';
        elements.segmentList.innerHTML = '';
        return;
    }

    // Sort clusters by share_of_corpus
    const sortedClusters = [...runData.clusters].sort((a, b) => (b.share_of_corpus || 0) - (a.share_of_corpus || 0));

    // Render Themes
    elements.themesList.innerHTML = sortedClusters.map((c, i) => `
        <div class="bg-surface hover-lift rounded-xl p-5 border border-gray-800 cursor-pointer transition-colors" onclick="openDrawer(${c.id})">
            <div class="flex justify-between items-start mb-3">
                <div class="flex items-center">
                    <span class="text-xl font-bold mr-3 text-spotify">#${i + 1}</span>
                    <h3 class="text-lg font-bold">${c.theme_label}</h3>
                </div>
                <div class="text-right">
                    <div class="text-xs text-textSecondary uppercase tracking-wide">Share</div>
                    <div class="font-semibold">${Math.round((c.share_of_corpus || 0) * 100)}%</div>
                </div>
            </div>
            <p class="text-textSecondary text-sm mb-4">${c.description}</p>
            <div class="w-full bg-gray-800 rounded-full h-1.5">
                <div class="bg-spotify h-1.5 rounded-full" style="width: ${Math.round((c.share_of_corpus || 0) * 100)}%"></div>
            </div>
        </div>
    `).join('');

    // Render Unmet Needs
    elements.needsList.innerHTML = sortedClusters.slice(0, 5).map(c => `
        <div class="flex items-start">
            <div class="w-1.5 h-1.5 rounded-full bg-spotify mt-2 mr-3 flex-shrink-0"></div>
            <p class="text-sm">${c.unmet_needs || 'Not specified'}</p>
        </div>
    `).join('');

    // Render JTBD
    elements.jtbdList.innerHTML = sortedClusters.slice(0, 3).map(c => `
        <div class="bg-surface p-4 rounded-lg border border-gray-800 text-sm italic border-l-2 border-l-spotify">
            "${c.jtbd_statement}"
        </div>
    `).join('');

    // Render Segments
    const segments = [...new Set(sortedClusters.map(c => c.user_segment).filter(Boolean))];
    elements.segmentList.innerHTML = segments.map((s, i) => {
        const patternClass = patterns[i % patterns.length];
        return `
        <div class="flex items-center justify-between">
            <span class="text-sm font-medium">${s}</span>
            <div class="w-16 h-4 rounded ${patternClass} border border-gray-700"></div>
        </div>
    `}).join('');
}

function openDrawer(clusterId) {
    if (!currentRunData) return;
    const cluster = currentRunData.clusters.find(c => c.id === clusterId);
    if (!cluster) return;

    elements.drawerTitle.textContent = cluster.theme_label;
    
    // Render feedback items as paraphrased evidence
    elements.drawerContent.innerHTML = `
        <div class="mb-6">
            <h4 class="text-xs uppercase text-textSecondary font-bold mb-2">Root Cause Hypothesis</h4>
            <p class="text-sm bg-background p-3 rounded border border-gray-800">${cluster.root_cause || 'N/A'}</p>
        </div>
        <h4 class="text-xs uppercase text-textSecondary font-bold mb-3">Raw Evidence</h4>
        <div class="space-y-3">
            ${cluster.feedback_items.map(fi => `
                <div class="p-3 bg-background rounded border border-gray-800 text-sm">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-xs font-semibold text-spotify px-2 py-0.5 bg-gray-900 rounded">${fi.source}</span>
                        <span class="text-xs text-textSecondary">${new Date(fi.date).toLocaleDateString()}</span>
                    </div>
                    <p class="text-gray-300">"${fi.text}"</p>
                </div>
            `).join('')}
        </div>
    `;

    elements.drawerOverlay.classList.remove('hidden');
    // slight delay for transition
    setTimeout(() => {
        elements.drawerOverlay.classList.remove('opacity-0');
        elements.evidenceDrawer.classList.remove('translate-x-full');
    }, 10);
}

function closeDrawer() {
    elements.drawerOverlay.classList.add('opacity-0');
    elements.evidenceDrawer.classList.add('translate-x-full');
    setTimeout(() => {
        elements.drawerOverlay.classList.add('hidden');
    }, 300);
}

init();
