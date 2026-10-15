/**
 * CRICBRAIN - Main Application Logic
 * Agentic AI Cricket Records Engine
 * Built by Suyog Shinde
 */

document.addEventListener("DOMContentLoaded", () => {
    // Current application state
    const state = {
        activeFormat: "test", // 'test', 'odi', 't20i', 'all'
        cachedData: {},
        hasApiKey: false,
        isLoading: false,
    };

    // DOM Elements
    const formatTabs = document.querySelectorAll(".format-tab-btn");
    const loadingContainer = document.getElementById("loading-agent-container");
    const resultsContainer = document.getElementById("results-content-container");
    const agentTrailSteps = document.getElementById("agent-trail-steps");
    const currentFormatTitle = document.getElementById("current-format-title");
    const formatDescription = document.getElementById("format-description");
    const dateCheckedLabel = document.getElementById("date-checked-label");
    const cutoffRuleNotice = document.getElementById("cutoff-rule-notice");

    // Single format result elements
    const singleFormatView = document.getElementById("single-format-view");
    const allFormatsView = document.getElementById("all-formats-view");
    const highestAvgCardContainer = document.getElementById("highest-avg-card-container");
    const batsmenPodiumList = document.getElementById("batsmen-podium-list");
    const bowlersPodiumList = document.getElementById("bowlers-podium-list");

    // Buttons
    const btnStartInnings = document.getElementById("btn-start-innings");
    const btnRefresh = document.getElementById("btn-refresh-stats");
    const btnDownloadTxt = document.getElementById("btn-download-txt");
    const btnPrintPdf = document.getElementById("btn-print-pdf");

    // Ask CRICBRAIN elements
    const askInput = document.getElementById("ask-cricbrain-input");
    const askBtn = document.getElementById("btn-ask-submit");
    const askAnswerBox = document.getElementById("ask-answer-box");
    const askAnswerText = document.getElementById("ask-answer-text");
    const askAnswerMeta = document.getElementById("ask-answer-meta");
    const quickChips = document.querySelectorAll(".chip-btn");

    // Modal elements
    const modalKey = document.getElementById("modal-api-key");
    const btnOpenKeyModal = document.getElementById("btn-open-key-modal");
    const btnCloseKeyModal = document.getElementById("btn-close-key-modal");
    const btnCancelKeyModal = document.getElementById("btn-cancel-key-modal");
    const btnSaveKey = document.getElementById("btn-save-key");
    const inputApiKey = document.getElementById("input-api-key");
    const groundingPill = document.getElementById("grounding-status-pill");

    // Celebration
    const sixOverlay = document.getElementById("six-celebration-overlay");
    const confettiCanvas = document.getElementById("confetti-canvas");

    // 1. INITIALIZE SERVER STATUS & TEASERS
    checkServerConfig();
    initTeaserCounters();
    initTiltCards();

    // 2. TAB CLICK HANDLERS
    formatTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const format = tab.getAttribute("data-format");
            if (format === state.activeFormat && !state.isLoading) return;
            switchFormat(format);
        });
    });

    // 3. START INNINGS BUTTON
    if (btnStartInnings) {
        btnStartInnings.addEventListener("click", (e) => {
            e.preventDefault();
            const target = document.getElementById("workspace-section");
            if (target) {
                target.scrollIntoView({ behavior: "smooth" });
            }
            if (!state.cachedData[state.activeFormat]) {
                fetchRecords(state.activeFormat);
            }
        });
    }

    // 4. REFRESH BUTTON
    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            fetchRecords(state.activeFormat, true);
        });
    }

    // 5. DOWNLOAD / PRINT HANDLERS
    if (btnDownloadTxt) {
        btnDownloadTxt.addEventListener("click", () => {
            window.location.href = `/api/export?format=${state.activeFormat}`;
        });
    }

    if (btnPrintPdf) {
        btnPrintPdf.addEventListener("click", () => {
            window.print();
        });
    }

    // 6. QUICK CHIPS FOR "ASK CRICBRAIN"
    quickChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const q = chip.getAttribute("data-query");
            if (askInput) {
                askInput.value = q;
                submitFollowUpQuestion(q);
            }
        });
    });

    if (askBtn && askInput) {
        askBtn.addEventListener("click", () => {
            const q = askInput.value.trim();
            if (q) submitFollowUpQuestion(q);
        });

        askInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const q = askInput.value.trim();
                if (q) submitFollowUpQuestion(q);
            }
        });
    }

    // 7. API KEY MODAL LOGIC
    if (btnOpenKeyModal) {
        btnOpenKeyModal.addEventListener("click", () => openKeyModal());
    }
    if (btnCloseKeyModal) {
        btnCloseKeyModal.addEventListener("click", () => closeKeyModal());
    }
    if (btnCancelKeyModal) {
        btnCancelKeyModal.addEventListener("click", () => closeKeyModal());
    }
    if (btnSaveKey) {
        btnSaveKey.addEventListener("click", () => saveApiKey());
    }

    function openKeyModal() {
        if (modalKey) {
            modalKey.classList.add("active");
            if (inputApiKey) inputApiKey.focus();
        }
    }

    function closeKeyModal() {
        if (modalKey) modalKey.classList.remove("active");
    }

    async function checkServerConfig() {
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
            if (data.status === "success") {
                state.hasApiKey = data.hasApiKey;
                updateGroundingStatusPill(data.hasApiKey);
                if (data.today && dateCheckedLabel) {
                    dateCheckedLabel.innerText = `Checked on ${data.today}`;
                }
            }
        } catch (err) {
            console.warn("Could not check server config:", err);
        }
    }

    function updateGroundingStatusPill(hasKey) {
        if (!groundingPill) return;
        if (hasKey) {
            groundingPill.className = "grounding-status-pill";
            groundingPill.innerHTML = `<span class="pulse-dot"></span> Google Search Grounding: Live`;
        } else {
            groundingPill.className = "grounding-status-pill needs-key";
            groundingPill.innerHTML = `<span class="pulse-dot"></span> Connect Gemini API Key`;
        }
    }

    async function saveApiKey() {
        const key = inputApiKey.value.trim();
        if (!key) {
            alert("Please enter a valid Gemini API key.");
            return;
        }

        try {
            const res = await fetch("/api/config/key", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ apiKey: key })
            });
            const data = await res.json();
            if (data.status === "success") {
                state.hasApiKey = true;
                updateGroundingStatusPill(true);
                closeKeyModal();
                inputApiKey.value = "";
                // Auto fetch active format
                fetchRecords(state.activeFormat, true);
            } else {
                alert(data.message || "Failed to save API key.");
            }
        } catch (err) {
            alert("Error communicating with server: " + err.message);
        }
    }

    // 8. FORMAT SWITCHER
    function switchFormat(format) {
        state.activeFormat = format;

        // Update active tab buttons
        formatTabs.forEach(tab => {
            if (tab.getAttribute("data-format") === format) {
                tab.classList.add("active");
            } else {
                tab.classList.remove("active");
            }
        });

        // Fetch or render cached data
        if (state.cachedData[format]) {
            renderResults(state.cachedData[format]);
        } else {
            fetchRecords(format);
        }
    }

    // 9. FETCH RECORDS WITH LIVE AGENT TRAIL
    async function fetchRecords(format, forceRefresh = false) {
        if (state.isLoading) return;
        state.isLoading = true;

        showLoadingState(format);

        try {
            const url = `/api/stats/${format}${forceRefresh ? "?refresh=true" : ""}`;
            const res = await fetch(url);
            const json = await res.json();

            if (res.status === 401 || json.status === "needs_key") {
                hideLoadingState();
                renderNeedsKeyMessage(json.message);
                state.isLoading = false;
                return;
            }

            if (json.status !== "success") {
                hideLoadingState();
                renderErrorMessage(json.message || "Could not retrieve records.");
                state.isLoading = false;
                return;
            }

            state.cachedData[format] = json.data;

            // Complete agent trail visual progression
            await simulateAgentTrailSteps(json.data.agent_trail || []);

            // Trigger "SIX!" celebration explosion
            triggerSixCelebration();

            hideLoadingState();
            renderResults(json.data);
        } catch (err) {
            hideLoadingState();
            renderErrorMessage("Network connection error: " + err.message);
        } finally {
            state.isLoading = false;
        }
    }

    function showLoadingState(format) {
        if (loadingContainer) loadingContainer.classList.add("active");
        if (resultsContainer) resultsContainer.style.opacity = "0.3";

        // Initial agent trail steps placeholder
        if (agentTrailSteps) {
            agentTrailSteps.innerHTML = `
                <div class="trail-step-item current" id="trail-step-1">
                    <div class="step-num-badge">1</div>
                    <div class="step-body-content">
                        <h4>Step 1: Understanding the question</h4>
                        <p>Setting criteria for Men's ${format.toUpperCase()} all-time records. Configuring cutoffs and tie rules.</p>
                    </div>
                </div>
                <div class="trail-step-item" id="trail-step-2">
                    <div class="step-num-badge">2</div>
                    <div class="step-body-content">
                        <h4>Step 2: Searching live cricket sources</h4>
                        <p>Dispatching Google Search grounding queries to ESPNcricinfo Statsguru & ACS Cricket tables...</p>
                    </div>
                </div>
                <div class="trail-step-item" id="trail-step-3">
                    <div class="step-num-badge">3</div>
                    <div class="step-body-content">
                        <h4>Step 3: Reading the tables</h4>
                        <p>Parsing career runs, career wickets, matches, and averages from verified cricket tables...</p>
                    </div>
                </div>
                <div class="trail-step-item" id="trail-step-4">
                    <div class="step-num-badge">4</div>
                    <div class="step-body-content">
                        <h4>Step 4: Checking the cutoff and ties</h4>
                        <p>Verifying minimum innings cutoff and comparing numbers for honest ties...</p>
                    </div>
                </div>
                <div class="trail-step-item" id="trail-step-5">
                    <div class="step-num-badge">5</div>
                    <div class="step-body-content">
                        <h4>Step 5: Building the answer</h4>
                        <p>Composing podium cards, attaching citations, and finalizing records...</p>
                    </div>
                </div>
            `;
        }
    }

    async function simulateAgentTrailSteps(trailData) {
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById(`trail-step-${i}`);
            if (stepEl) {
                stepEl.classList.remove("current");
                stepEl.classList.add("completed");
            }
            const nextStepEl = document.getElementById(`trail-step-${i + 1}`);
            if (nextStepEl) {
                nextStepEl.classList.add("current");
            }
            // Brief visual pacing
            await new Promise(r => setTimeout(r, 220));
        }
    }

    function hideLoadingState() {
        if (loadingContainer) loadingContainer.classList.remove("active");
        if (resultsContainer) resultsContainer.style.opacity = "1";
    }

    // 10. RENDER RESULTS
    function renderResults(data) {
        if (!data) return;

        // Update header details
        if (currentFormatTitle) currentFormatTitle.innerHTML = `<span>🏏</span> ${data.display_name || data.format}`;
        if (formatDescription) formatDescription.innerText = data.description || "All-time men's international cricket career records.";
        if (dateCheckedLabel) dateCheckedLabel.innerText = `Checked on ${data.checked_on || 'Today'}`;
        if (cutoffRuleNotice) {
            cutoffRuleNotice.innerText = data.cutoff_label || (data.format_key === 'all' ? 'All formats comparison' : 'Minimum innings cutoff applied');
        }

        if (data.format_key === "all") {
            renderAllFormatsView(data);
        } else {
            renderSingleFormatView(data);
        }

        // Re-initialize 3D tilt on newly rendered cards
        initTiltCards();
    }

    function renderSingleFormatView(data) {
        if (singleFormatView) singleFormatView.style.display = "block";
        if (allFormatsView) allFormatsView.style.display = "none";

        // 1. HIGHEST AVERAGE HIGHLIGHT CARD WITH GLOWING RING
        const ha = data.highest_average || {};
        const avgVal = ha.average || "Could not verify";
        const cutoffText = data.cutoff_label || ha.cutoff_applied || "Minimum cutoff applied";

        if (highestAvgCardContainer) {
            highestAvgCardContainer.innerHTML = `
                <div class="highlight-avg-card">
                    <div class="avg-glowing-ring">
                        <span class="ring-number">${avgVal}</span>
                        <span class="ring-unit">Career Avg</span>
                    </div>
                    <div class="avg-info-group">
                        <div class="cutoff-rule-badge">🛡️ ${cutoffText}</div>
                        <h3>${ha.player || 'Player'}</h3>
                        <div class="country-tag">Representing ${ha.country || 'International'}</div>
                        <div class="avg-stats-summary">
                            <span class="stat-item">Innings Batted: <strong>${ha.innings || 'N/A'}</strong></span>
                            <span class="stat-item">Career Runs: <strong>${ha.runs ? Number(ha.runs).toLocaleString() : 'N/A'}</strong></span>
                            <span class="stat-item">Matches: <strong>${ha.matches || 'N/A'}</strong></span>
                        </div>
                    </div>
                    <div class="avg-source-box">
                        <span class="source-verified-label" style="font-size:0.75rem; color:#94a3b8;">Official Grounded Source</span>
                        <a href="${ha.source_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-source-link">
                            <span>🔗</span> View Source Table
                        </a>
                    </div>
                </div>
            `;
        }

        // 2. TOP 5 BATSMEN PODIUM
        if (batsmenPodiumList) {
            const batsmen = data.top_batsmen || [];
            batsmenPodiumList.innerHTML = batsmen.map((b, idx) => {
                const rankClass = idx === 0 ? "rank-gold" : (idx === 1 ? "rank-silver" : (idx === 2 ? "rank-bronze" : "rank-standard"));
                const runsDisplay = b.runs !== undefined && b.runs !== null ? Number(b.runs).toLocaleString() : "Could not verify";
                const tieBadge = b.is_tie ? `<span class="tie-honesty-tag">🤝 Tied Rank</span>` : "";

                return `
                    <div class="record-card-3d ${rankClass}">
                        <div class="card-shine"></div>
                        <div class="record-card-header">
                            <div class="rank-badge-group">
                                <div class="rank-badge">${b.display_rank || (idx + 1)}</div>
                                ${tieBadge}
                            </div>
                            <div class="player-main-stat">
                                <div class="stat-huge-number">${runsDisplay}</div>
                                <div class="stat-unit-label">Career Runs</div>
                            </div>
                        </div>
                        <div class="player-identity">
                            <h4>${b.player || 'Player Name'}</h4>
                            <div class="player-country">${b.country || 'International'}</div>
                        </div>
                        <div class="card-metrics-row">
                            <span class="metric-pill">Innings: <strong>${b.innings || 'N/A'}</strong></span>
                            <span class="metric-pill">Matches: <strong>${b.matches || 'N/A'}</strong></span>
                            <span class="metric-pill">Average: <strong>${b.average || 'N/A'}</strong></span>
                            <a href="${b.source_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-source-link" style="padding:0.25rem 0.6rem; font-size:0.72rem;">
                                <span>🔗</span> Source
                            </a>
                        </div>
                    </div>
                `;
            }).join("");
        }

        // 3. TOP 5 BOWLERS PODIUM
        if (bowlersPodiumList) {
            const bowlers = data.top_bowlers || [];
            bowlersPodiumList.innerHTML = bowlers.map((bw, idx) => {
                const rankClass = idx === 0 ? "rank-gold" : (idx === 1 ? "rank-silver" : (idx === 2 ? "rank-bronze" : "rank-standard"));
                const wktsDisplay = bw.wickets !== undefined && bw.wickets !== null ? Number(bw.wickets).toLocaleString() : "Could not verify";
                const tieBadge = bw.is_tie ? `<span class="tie-honesty-tag">🤝 Tied Rank</span>` : "";

                return `
                    <div class="record-card-3d ${rankClass}">
                        <div class="card-shine"></div>
                        <div class="record-card-header">
                            <div class="rank-badge-group">
                                <div class="rank-badge">${bw.display_rank || (idx + 1)}</div>
                                ${tieBadge}
                            </div>
                            <div class="player-main-stat">
                                <div class="stat-huge-number">${wktsDisplay}</div>
                                <div class="stat-unit-label">Career Wickets</div>
                            </div>
                        </div>
                        <div class="player-identity">
                            <h4>${bw.player || 'Player Name'}</h4>
                            <div class="player-country">${bw.country || 'International'}</div>
                        </div>
                        <div class="card-metrics-row">
                            <span class="metric-pill">Innings: <strong>${bw.innings || 'N/A'}</strong></span>
                            <span class="metric-pill">Matches: <strong>${bw.matches || 'N/A'}</strong></span>
                            <span class="metric-pill">Avg/Econ: <strong>${bw.average || 'N/A'}</strong></span>
                            <a href="${bw.source_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-source-link" style="padding:0.25rem 0.6rem; font-size:0.72rem;">
                                <span>🔗</span> Source
                            </a>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    function renderAllFormatsView(data) {
        if (singleFormatView) singleFormatView.style.display = "none";
        if (allFormatsView) allFormatsView.style.display = "block";

        const formatsData = data.formats_data || {};
        const formatKeys = ["test", "odi", "t20i"];

        const html = `
            <div class="all-formats-grid">
                ${formatKeys.map(k => {
                    const fd = formatsData[k];
                    if (!fd) {
                        return `
                            <div class="format-column-box">
                                <h3>${k.toUpperCase()}</h3>
                                <p style="color:#ef4444;">Could not load data for ${k.toUpperCase()}.</p>
                            </div>
                        `;
                    }

                    const topBat = fd.top_batsmen ? fd.top_batsmen[0] : null;
                    const topBwl = fd.top_bowlers ? fd.top_bowlers[0] : null;
                    const ha = fd.highest_average || {};

                    return `
                        <div class="format-column-box">
                            <div class="format-col-header">
                                <h3>${fd.display_name || k.toUpperCase()}</h3>
                                <div class="col-cutoff">🛡️ ${fd.cutoff_label}</div>
                            </div>

                            <!-- Highest Average Highlight -->
                            <div style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.4); border-radius:12px; padding:0.9rem; text-align:center;">
                                <div style="font-size:0.75rem; color:#f59e0b; font-weight:700; text-transform:uppercase;">Highest Batting Average</div>
                                <div style="font-size:1.8rem; font-weight:800; color:#fff; font-family:var(--font-heading);">${ha.average || 'N/A'}</div>
                                <div style="font-weight:700; color:#fff; font-size:1rem;">${ha.player || 'Player'}</div>
                                <div style="font-size:0.78rem; color:#94a3b8;">${ha.innings || 'N/A'} innings | ${ha.runs || 'N/A'} runs</div>
                                <div style="margin-top:0.4rem;">
                                    <a href="${ha.source_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-source-link" style="font-size:0.7rem; padding:0.2rem 0.5rem;">🔗 Source</a>
                                </div>
                            </div>

                            <!-- Top 5 Batsmen -->
                            <div>
                                <h4 style="font-size:0.95rem; font-weight:700; color:#38bdf8; margin-bottom:0.6rem;">Top 5 Batsmen (Runs)</h4>
                                <div style="display:flex; flex-direction:column; gap:0.5rem;">
                                    ${(fd.top_batsmen || []).map((b, i) => `
                                        <div style="background:rgba(255,255,255,0.04); border-radius:8px; padding:0.5rem 0.75rem; display:flex; justify-content:space-between; align-items:center; font-size:0.82rem;">
                                            <div>
                                                <strong>#${b.display_rank || (i+1)} ${b.player}</strong>
                                                <div style="font-size:0.72rem; color:#94a3b8;">${b.country} | ${b.innings} inns</div>
                                            </div>
                                            <div style="text-align:right;">
                                                <div style="font-weight:800; color:#fff;">${Number(b.runs).toLocaleString()}</div>
                                                <a href="${b.source_url || '#'}" target="_blank" rel="noopener noreferrer" style="font-size:0.68rem; color:#38bdf8; text-decoration:none;">source</a>
                                            </div>
                                        </div>
                                    `).join("")}
                                </div>
                            </div>

                            <!-- Top 5 Bowlers -->
                            <div>
                                <h4 style="font-size:0.95rem; font-weight:700; color:#34d399; margin-bottom:0.6rem;">Top 5 Bowlers (Wickets)</h4>
                                <div style="display:flex; flex-direction:column; gap:0.5rem;">
                                    ${(fd.top_bowlers || []).map((bw, i) => `
                                        <div style="background:rgba(255,255,255,0.04); border-radius:8px; padding:0.5rem 0.75rem; display:flex; justify-content:space-between; align-items:center; font-size:0.82rem;">
                                            <div>
                                                <strong>#${bw.display_rank || (i+1)} ${bw.player}</strong>
                                                <div style="font-size:0.72rem; color:#94a3b8;">${bw.country} | ${bw.innings} inns</div>
                                            </div>
                                            <div style="text-align:right;">
                                                <div style="font-weight:800; color:#fff;">${Number(bw.wickets).toLocaleString()}</div>
                                                <a href="${bw.source_url || '#'}" target="_blank" rel="noopener noreferrer" style="font-size:0.68rem; color:#38bdf8; text-decoration:none;">source</a>
                                            </div>
                                        </div>
                                    `).join("")}
                                </div>
                            </div>
                        </div>
                    `;
                }).join("")}
            </div>
        `;

        allFormatsView.innerHTML = html;
    }

    function renderNeedsKeyMessage(message) {
        if (singleFormatView) singleFormatView.style.display = "block";
        if (allFormatsView) allFormatsView.style.display = "none";

        if (highestAvgCardContainer) {
            highestAvgCardContainer.innerHTML = `
                <div style="background:rgba(245,158,11,0.12); border:1.5px solid rgba(245,158,11,0.5); border-radius:18px; padding:2rem; text-align:center;">
                    <h3 style="color:#ffd700; font-family:var(--font-heading); margin-bottom:0.5rem;">🔑 API Key Required for Live Grounding</h3>
                    <p style="color:#e2e8f0; font-size:0.95rem; margin-bottom:1.25rem; max-width:620px; margin-left:auto; margin-right:auto;">
                        ${message || "Gemini API key is required on the server to execute live Google Search grounding across official cricket record tables."}
                    </p>
                    <button class="btn-start-innings" style="font-size:0.95rem; padding:0.75rem 1.8rem;" onclick="document.getElementById('modal-api-key').classList.add('active')">
                        Connect Gemini API Key Securely
                    </button>
                    <p style="font-size:0.75rem; color:#94a3b8; margin-top:0.8rem;">
                        Your key is saved only in your local server's .env file and is never exposed in browser code.
                    </p>
                </div>
            `;
        }
        if (batsmenPodiumList) batsmenPodiumList.innerHTML = "";
        if (bowlersPodiumList) bowlersPodiumList.innerHTML = "";
    }

    function renderErrorMessage(message) {
        if (singleFormatView) singleFormatView.style.display = "block";
        if (allFormatsView) allFormatsView.style.display = "none";

        if (highestAvgCardContainer) {
            highestAvgCardContainer.innerHTML = `
                <div style="background:rgba(239,68,68,0.12); border:1.5px solid rgba(239,68,68,0.5); border-radius:18px; padding:2rem; text-align:center;">
                    <h3 style="color:#f87171; font-family:var(--font-heading); margin-bottom:0.5rem;">⚠️ Search Verification Notice</h3>
                    <p style="color:#fca5a5; font-size:0.95rem; margin-bottom:1rem; max-width:600px; margin-left:auto; margin-right:auto;">
                        ${message}
                    </p>
                    <button class="btn-secondary-innings" onclick="window.location.reload()">
                        Retry Search
                    </button>
                </div>
            `;
        }
    }

    // 11. "ASK CRICBRAIN" FOLLOW-UP SUBMISSION
    async function submitFollowUpQuestion(question) {
        if (!question) return;

        if (askAnswerBox) {
            askAnswerBox.classList.add("active");
            askAnswerText.innerHTML = `<span style="color:#38bdf8;">Searching live cricket sources via Gemini Grounding...</span>`;
            if (askAnswerMeta) askAnswerMeta.innerHTML = "";
        }

        try {
            const res = await fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    format: state.activeFormat.toUpperCase()
                })
            });

            const json = await res.json();

            if (res.status === 401 || json.status === "needs_key") {
                askAnswerText.innerHTML = `<span style="color:#fbbf24;">Please connect your Gemini API key in the top settings bar to enable live grounded follow-ups.</span>`;
                return;
            }

            if (json.status !== "success") {
                askAnswerText.innerHTML = `<span style="color:#f87171;">${json.message || 'Could not verify follow-up stat.'}</span>`;
                return;
            }

            const data = json.data;
            askAnswerText.innerHTML = `
                <div style="margin-bottom:0.5rem; font-weight:700; color:#38bdf8;">Q: "${data.question}"</div>
                <div>${data.answer}</div>
            `;

            const sourcesHtml = (data.sources || []).map(s => `
                <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="btn-source-link" style="font-size:0.75rem; padding:0.25rem 0.55rem;">
                    🔗 ${s.title || 'Source'}
                </a>
            `).join("");

            askAnswerMeta.innerHTML = `
                <div>Checked on ${data.checked_on} • ${data.lag_note}</div>
                <div style="display:flex; gap:0.4rem; flex-wrap:wrap;">${sourcesHtml}</div>
            `;
        } catch (err) {
            askAnswerText.innerHTML = `<span style="color:#f87171;">Error searching follow-up: ${err.message}</span>`;
        }
    }

    // 12. CELEBRATION "SIX!" EXPLOSION & CONFETTI
    function triggerSixCelebration() {
        if (!sixOverlay || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

        sixOverlay.classList.add("active");
        runConfettiAnimation();

        setTimeout(() => {
            sixOverlay.classList.remove("active");
        }, 1200);
    }

    function runConfettiAnimation() {
        if (!confettiCanvas) return;
        const ctx = confettiCanvas.getContext("2d");
        confettiCanvas.width = window.innerWidth;
        confettiCanvas.height = window.innerHeight;

        const particles = [];
        const colors = ["#ffd700", "#dc2626", "#10b981", "#38bdf8", "#ffffff"];

        for (let i = 0; i < 75; i++) {
            particles.push({
                x: window.innerWidth / 2,
                y: window.innerHeight / 2,
                vx: (Math.random() - 0.5) * 18,
                vy: (Math.random() - 0.5) * 18 - 4,
                size: Math.random() * 8 + 4,
                color: colors[Math.floor(Math.random() * colors.length)],
                rotation: Math.random() * 360,
                vr: (Math.random() - 0.5) * 10,
                opacity: 1
            });
        }

        let animId;
        function update() {
            ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
            let alive = false;

            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.vy += 0.35; // gravity
                p.rotation += p.vr;
                p.opacity -= 0.015;

                if (p.opacity > 0) {
                    alive = true;
                    ctx.save();
                    ctx.globalAlpha = p.opacity;
                    ctx.translate(p.x, p.y);
                    ctx.rotate((p.rotation * Math.PI) / 180);
                    ctx.fillStyle = p.color;
                    ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
                    ctx.restore();
                }
            });

            if (alive) {
                animId = requestAnimationFrame(update);
            } else {
                ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
                cancelAnimationFrame(animId);
            }
        }
        update();
    }

    // 13. ANIMATED TEASER COUNTERS
    function initTeaserCounters() {
        const counters = document.querySelectorAll(".counter-number");
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

        counters.forEach(counter => {
            const target = parseFloat(counter.getAttribute("data-target"));
            const isFloat = counter.getAttribute("data-is-float") === "true";
            let current = 0;
            const duration = 2000;
            const startTime = performance.now();

            function tick(now) {
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // easeOutExpo
                const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                current = target * ease;

                if (isFloat) {
                    counter.innerText = current.toFixed(2);
                } else {
                    counter.innerText = Math.floor(current).toLocaleString();
                }

                if (progress < 1) {
                    requestAnimationFrame(tick);
                }
            }
            requestAnimationFrame(tick);
        });
    }

    // 14. 3D TILT EFFECT ON CARDS
    function initTiltCards() {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

        const tiltCards = document.querySelectorAll(".record-card-3d, .teaser-card");

        tiltCards.forEach(card => {
            card.addEventListener("mousemove", (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = ((y - centerY) / centerY) * -8;
                const rotateY = ((x - centerX) / centerX) * 8;

                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;

                // Position sheen shine
                const shine = card.querySelector(".card-shine");
                if (shine) {
                    shine.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(255, 255, 255, 0.18) 0%, transparent 70%)`;
                }
            });

            card.addEventListener("mouseleave", () => {
                card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
            });
        });
    }
});
