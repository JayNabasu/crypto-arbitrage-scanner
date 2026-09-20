let isPolling = true;
let pollTimer = null;

const latencyVal = document.getElementById('latencyVal');
const pairsVal = document.getElementById('pairsVal');
const oppCountVal = document.getElementById('oppCountVal');
const oppsContainer = document.getElementById('oppsContainer');
const ratesTbody = document.getElementById('ratesTbody');
const togglePollingBtn = document.getElementById('togglePollingBtn');
const manualScanBtn = document.getElementById('manualScanBtn');
const livePill = document.getElementById('livePill');

// WebAudio synthesize arbitrage notification beep
let audioCtx = null;
function playArbitrageChime() {
    try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.25);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.25);
    } catch(e) {}
}

async function fetchMarketScan() {
    try {
        const res = await fetch('/api/v1/scan');
        if (!res.ok) return;
        const data = await res.json();
        renderDashboard(data);
    } catch (err) {
        console.error("Scan fetch error:", err);
    }
}

function renderDashboard(data) {
    latencyVal.textContent = `${data.latency_ms} ms`;
    pairsVal.textContent = `${data.currencies_count} / ${data.pairs_count}`;
    oppCountVal.textContent = data.opportunities.length;

    // Opportunities rendering
    if (data.opportunities.length === 0) {
        oppsContainer.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
                No negative cycles detected above 0.05% net fee hurdle. Cross-market prices are currently in equilibrium.
            </div>
        `;
    } else {
        playArbitrageChime();
        oppsContainer.innerHTML = data.opportunities.map(opp => `
            <div class="opp-card">
                <div class="opp-top">
                    <div class="opp-path">⚡ ${opp.path}</div>
                    <div class="opp-yield">+${opp.profit_pct.toFixed(3)}%</div>
                </div>
                <div class="opp-details">
                    <div>Multiplier: <strong>${opp.effective_multiplier}x</strong></div>
                    <div>Legs: <strong>${opp.currencies.length - 1} steps</strong></div>
                    <div>Rates: <code>[${opp.rates.join(', ')}]</code></div>
                    <div>Net Fee: <strong>${(data.fee_pct * 100).toFixed(3)}% / leg</strong></div>
                </div>
            </div>
        `).join('');
    }

    // Rates matrix rendering
    const currencies = ["USDT", "BTC", "ETH", "SOL", "BNB"];
    let rowsHtml = '';
    for (const fromC of currencies) {
        let cellsHtml = `<td><strong>${fromC}</strong></td>`;
        for (const toC of currencies) {
            if (fromC === toC) {
                cellsHtml += `<td style="color: var(--text-muted); opacity: 0.3;">1.000</td>`;
            } else {
                const rate = data.rates[fromC]?.[toC];
                cellsHtml += `<td>${rate !== undefined ? rate : '-'}</td>`;
            }
        }
        rowsHtml += `<tr>${cellsHtml}</tr>`;
    }
    ratesTbody.innerHTML = rowsHtml;
}

togglePollingBtn.addEventListener('click', () => {
    isPolling = !isPolling;
    if (isPolling) {
        togglePollingBtn.textContent = 'Pause Feed';
        livePill.innerHTML = '<span class="dot"></span><span>ENGINE POLLING (1s)</span>';
        startPolling();
    } else {
        togglePollingBtn.textContent = 'Resume Feed';
        livePill.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:#94a3b8;display:inline-block;"></span><span>FEED PAUSED</span>';
        clearInterval(pollTimer);
    }
});

manualScanBtn.addEventListener('click', () => {
    fetchMarketScan();
});

function startPolling() {
    clearInterval(pollTimer);
    fetchMarketScan();
    pollTimer = setInterval(fetchMarketScan, 1200);
}

// Initial fetch
startPolling();
