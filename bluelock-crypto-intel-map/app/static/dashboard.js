/**
 * dashboard.js
 * ─────────────
 * BlueLock Crypto Intel Dashboard — frontend logic.
 * Handles: API calls, results rendering, graph, table filtering, case management.
 */

// ── State ──────────────────────────────────────────────────────
let currentResult = null;    // Last successful analysis result
let currentAddress = "";
let currentChain = "";
let activeFilter = "all";
let cyInstance = null;       // Cytoscape graph instance

// ── DOM refs ───────────────────────────────────────────────────
const walletInput  = document.getElementById("wallet-input");
const chainSelect  = document.getElementById("chain-select");
const analyzeBtn   = document.getElementById("analyze-btn");
const btnText      = document.getElementById("btn-text");
const btnSpinner   = document.getElementById("btn-spinner");
const welcomePanel = document.getElementById("welcome-panel");
const resultsArea  = document.getElementById("results-area");
const errorBanner  = document.getElementById("error-banner");
const warningBanner= document.getElementById("warning-banner");

// ══ INIT ═══════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  loadApiStatus();
  loadCases();
  setupEventListeners();
});

// ── Event listeners ────────────────────────────────────────────
function setupEventListeners() {
  analyzeBtn.addEventListener("click", runAnalysis);
  walletInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runAnalysis();
  });

  document.getElementById("settings-toggle").addEventListener("click", openSettings);
  document.getElementById("settings-close").addEventListener("click", closeSettings);
  document.querySelector(".modal-backdrop")?.addEventListener("click", closeSettings);

  document.getElementById("save-case-btn").addEventListener("click", saveCase);
  document.getElementById("export-btn").addEventListener("click", exportJson);
  document.getElementById("refresh-cases").addEventListener("click", loadCases);

  // Transaction filter buttons
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.dataset.filter;
      applyTxFilter();
    });
  });
}

// ══ API STATUS ══════════════════════════════════════════════════
async function loadApiStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    renderApiStatus(data.chains);
  } catch (e) {
    console.error("Failed to load API status", e);
  }
}

function renderApiStatus(chains) {
  const container = document.getElementById("api-status-list");
  const detailContainer = document.getElementById("api-keys-detail");
  let html = "";
  let detailHtml = "";
  let anyKey = false;

  for (const [id, info] of Object.entries(chains)) {
    const hasKey = info.has_key;
    if (hasKey) anyKey = true;
    const statusClass = hasKey ? "key-ok" : "key-missing";
    const statusText  = hasKey ? "CONFIGURED" : "MISSING";

    html += `
      <div class="api-row">
        <span class="api-chain">${info.name}</span>
        <span class="api-key-status ${statusClass}">${statusText}</span>
      </div>`;

    const envVar = id.toUpperCase() + "SCAN_API_KEY";
    const displayEnv = id === "ethereum" ? "ETHERSCAN_API_KEY" :
                       id === "bsc"      ? "BSCSCAN_API_KEY" :
                       id === "polygon"  ? "POLYGONSCAN_API_KEY" :
                       id === "arbitrum" ? "ARBISCAN_API_KEY" :
                       id === "base"     ? "BASESCAN_API_KEY" : envVar;

    detailHtml += `
      <div class="api-key-row">
        <span class="api-key-name">${info.name}</span>
        <code class="api-key-env">${displayEnv}</code>
        <span class="api-key-stat ${hasKey ? "key-configured" : "key-not-configured"}">
          ${hasKey ? "✓ SET" : "✗ NOT SET"}
        </span>
      </div>`;
  }

  container.innerHTML = html;
  if (detailContainer) detailContainer.innerHTML = detailHtml;

  // Update status dot
  const dot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  if (anyKey) {
    dot.className = "status-dot active";
    statusText.textContent = "API CONNECTED";
  }
}

// ══ ANALYSIS ═══════════════════════════════════════════════════
async function runAnalysis() {
  const address = walletInput.value.trim();
  const chain   = chainSelect.value;

  if (!address) {
    showError("Please enter a wallet address.");
    return;
  }

  setLoading(true);
  hideAlerts();

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, chain }),
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || "Analysis failed. Check the server logs.");
      setLoading(false);
      return;
    }

    if (data.warning) {
      showWarning(data.warning);
    }

    currentResult  = data;
    currentAddress = address;
    currentChain   = chain;

    renderResults(data);
    loadCases(); // Refresh in case this was previously saved

  } catch (e) {
    showError("Could not reach the server. Make sure run.bat is running.");
    console.error(e);
  }

  setLoading(false);
}

function setLoading(loading) {
  analyzeBtn.disabled = loading;
  btnText.classList.toggle("hidden", loading);
  btnSpinner.classList.toggle("hidden", !loading);
}

// ══ RENDER RESULTS ══════════════════════════════════════════════
function renderResults(data) {
  welcomePanel.classList.add("hidden");
  resultsArea.classList.remove("hidden");

  renderSummary(data);
  renderRiskNotes(data.risk_notes || []);
  renderGraph(data.graph_nodes || [], data.graph_edges || []);
  renderTransactions(data.transactions || []);
  loadCaseNotes(data.address, data.chain);
}

// ── Summary Card ───────────────────────────────────────────────
function renderSummary(data) {
  const s = data.summary;
  const chainName = chainNameFor(data.chain);
  document.getElementById("chain-badge").textContent = data.chain.toUpperCase();

  const explorerBase = getExplorerBase(data.chain);
  const explorerLink = document.getElementById("explorer-link");
  explorerLink.href = `${explorerBase}/address/${data.address}`;

  const grid = document.getElementById("summary-grid");

  if (!s) {
    grid.innerHTML = `
      <div class="summary-cell">
        <div class="summary-cell-label">ADDRESS</div>
        <div class="summary-cell-value">${truncate(data.address, 14)}</div>
      </div>`;
    return;
  }

  grid.innerHTML = `
    <div class="summary-cell">
      <div class="summary-cell-label">ADDRESS</div>
      <div class="summary-cell-value mono" style="font-size:10px;">${s.address}</div>
    </div>
    <div class="summary-cell">
      <div class="summary-cell-label">CHAIN</div>
      <div class="summary-cell-value accent-blue">${chainName}</div>
    </div>
    <div class="summary-cell">
      <div class="summary-cell-label">TRANSACTIONS (LOADED)</div>
      <div class="summary-cell-value">${s.tx_count.toLocaleString()}</div>
    </div>
    <div class="summary-cell">
      <div class="summary-cell-label">TOKEN TRANSFERS</div>
      <div class="summary-cell-value">${s.token_tx_count.toLocaleString()}</div>
    </div>
    <div class="summary-cell">
      <div class="summary-cell-label">FIRST SEEN</div>
      <div class="summary-cell-value">${s.first_seen || "—"}</div>
    </div>
    <div class="summary-cell">
      <div class="summary-cell-label">LAST SEEN</div>
      <div class="summary-cell-value">${s.last_seen || "—"}</div>
    </div>
    <div class="summary-cell">
      <div class="summary-cell-label">NATIVE BALANCE</div>
      <div class="summary-cell-value accent-green">${s.native_balance || "0"} ${s.symbol}</div>
    </div>`;
}

// ── Risk Notes ─────────────────────────────────────────────────
function renderRiskNotes(notes) {
  const body = document.getElementById("risk-notes-body");

  if (!notes || notes.length === 0) {
    body.innerHTML = '<div class="empty-state">No observations flagged for this wallet.</div>';
    return;
  }

  const icons = { info: "ℹ", warning: "⚠", alert: "⛔" };

  body.innerHTML = notes.map(n => `
    <div class="risk-note ${n.level}">
      <span class="risk-icon">${icons[n.level] || "ℹ"}</span>
      <div>
        <span class="risk-code">${n.code}</span>
        ${escapeHtml(n.message)}
      </div>
    </div>
  `).join("");
}

// ── Cytoscape Graph ────────────────────────────────────────────
const nodeColors = {
  target:       "#3b82f6",
  exchange:     "#a855f7",
  dex:          "#22d3ee",
  bridge:       "#f97316",
  counterparty: "#4a5a6a",
  contract:     "#64748b",
};

function renderGraph(nodes, edges) {
  if (cyInstance) {
    cyInstance.destroy();
    cyInstance = null;
  }

  if (!nodes || nodes.length === 0) return;

  const elements = [];

  nodes.forEach(n => {
    elements.push({
      data: {
        id: n.id,
        label: n.label,
        node_type: n.node_type,
        tx_count: n.tx_count,
      }
    });
  });

  edges.forEach(e => {
    elements.push({
      data: {
        source: e.source,
        target: e.target,
        tx_count: e.tx_count,
      }
    });
  });

  cyInstance = cytoscape({
    container: document.getElementById("cy"),
    elements,
    style: [
      {
        selector: "node",
        style: {
          "background-color": ele => nodeColors[ele.data("node_type")] || "#4a5a6a",
          "label": "data(label)",
          "font-family": "IBM Plex Mono, monospace",
          "font-size": 9,
          "color": "#9aa6b4",
          "text-valign": "bottom",
          "text-margin-y": 4,
          "width": ele => {
            const type = ele.data("node_type");
            if (type === "target") return 32;
            const tc = ele.data("tx_count") || 1;
            return Math.max(12, Math.min(26, 10 + tc * 0.5));
          },
          "height": ele => {
            const type = ele.data("node_type");
            if (type === "target") return 32;
            const tc = ele.data("tx_count") || 1;
            return Math.max(12, Math.min(26, 10 + tc * 0.5));
          },
          "border-width": ele => ele.data("node_type") === "target" ? 2 : 1,
          "border-color": ele => nodeColors[ele.data("node_type")] || "#4a5a6a",
          "border-opacity": 0.7,
        }
      },
      {
        selector: "edge",
        style: {
          "width": 1,
          "line-color": "#252a30",
          "target-arrow-color": "#252a30",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "opacity": 0.7,
        }
      },
      {
        selector: "node:selected",
        style: {
          "border-width": 3,
          "border-color": "#fff",
          "border-opacity": 0.8,
        }
      }
    ],
    layout: {
      name: "cose",
      idealEdgeLength: 80,
      nodeOverlap: 20,
      refresh: 20,
      fit: true,
      padding: 24,
      randomize: false,
      componentSpacing: 100,
      nodeRepulsion: 450000,
      edgeElasticity: 100,
      nestingFactor: 5,
      gravity: 80,
      numIter: 1000,
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0,
    },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
    autounselectify: false,
  });

  // Click node to filter transactions
  cyInstance.on("tap", "node", evt => {
    const nodeId = evt.target.data("id");
    if (nodeId !== currentAddress.toLowerCase()) {
      walletInput.value = nodeId;
      // Don't auto-run — let user confirm
    }
  });
}

// ── Transaction Table ──────────────────────────────────────────
function renderTransactions(txs) {
  const tbody = document.getElementById("tx-body");
  tbody.dataset.allTxs = JSON.stringify(txs);
  applyTxFilter();
}

function applyTxFilter() {
  const tbody  = document.getElementById("tx-body");
  const empty  = document.getElementById("tx-empty");
  const rawStr = tbody.dataset.allTxs;
  if (!rawStr) return;
  const allTxs = JSON.parse(rawStr);
  const explorerBase = getExplorerBase(currentChain);

  let filtered = allTxs;
  if (activeFilter === "in")      filtered = allTxs.filter(t => t.direction === "in");
  if (activeFilter === "out")     filtered = allTxs.filter(t => t.direction === "out");
  if (activeFilter === "dex")     filtered = allTxs.filter(t => t.tx_type === "dex");
  if (activeFilter === "flagged") filtered = allTxs.filter(t => t.flagged);

  if (filtered.length === 0) {
    tbody.innerHTML = "";
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");

  tbody.innerHTML = filtered.map(tx => {
    const dirClass = tx.direction === "in" ? "dir-in" : "dir-out";
    const dirLabel = tx.direction.toUpperCase();
    const typeClass = `type-${tx.tx_type}`;
    const typeLabel = tx.tx_type.toUpperCase();
    const flagHtml  = tx.flagged ? '<span class="flag-icon">⚑</span>' : "";
    const cpLabel   = tx.counterparty_label
      ? `<br><span class="cp-label">${escapeHtml(tx.counterparty_label)}</span>` : "";
    const tokenHtml = tx.token_symbol ? `<span class="type-badge type-token">${escapeHtml(tx.token_symbol)}</span>` : "—";
    const hashLink  = tx.hash
      ? `<a class="tx-hash" href="${explorerBase}/tx/${tx.hash}" target="_blank" rel="noopener">${tx.hash_short}</a>`
      : "—";

    return `
      <tr class="${tx.flagged ? "flagged" : ""}">
        <td class="mono" style="font-size:10px;white-space:nowrap;">${tx.timestamp}</td>
        <td><span class="type-badge ${typeClass}">${typeLabel}</span></td>
        <td><span class="dir-badge ${dirClass}">${dirLabel}</span></td>
        <td style="max-width:160px;overflow:hidden;">
          ${flagHtml}
          <span class="mono" style="font-size:10px;">${truncate(tx.counterparty, 16)}</span>
          ${cpLabel}
        </td>
        <td class="mono" style="font-size:11px;">${tx.value}</td>
        <td>${tokenHtml}</td>
        <td>${hashLink}</td>
      </tr>`;
  }).join("");
}

// ══ CASE NOTES ══════════════════════════════════════════════════
async function loadCaseNotes(address, chain) {
  try {
    const res = await fetch(`/api/cases/${encodeURIComponent(address)}/${chain}`);
    if (res.ok) {
      const c = await res.json();
      document.getElementById("case-label").value = c.label || "";
      document.getElementById("case-tags").value  = (JSON.parse(c.tags || "[]")).join(", ");
      document.getElementById("case-notes").value = c.notes || "";
    } else {
      document.getElementById("case-label").value = "";
      document.getElementById("case-tags").value  = "";
      document.getElementById("case-notes").value = "";
    }
  } catch {}
}

async function saveCase() {
  if (!currentAddress) return;
  const label  = document.getElementById("case-label").value.trim();
  const tagsRaw= document.getElementById("case-tags").value.trim();
  const notes  = document.getElementById("case-notes").value.trim();
  const tags   = tagsRaw ? tagsRaw.split(",").map(t => t.trim()).filter(Boolean) : [];

  const saveStatus = document.getElementById("save-status");

  try {
    const res = await fetch("/api/cases/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: currentAddress, chain: currentChain, label, tags, notes }),
    });
    if (res.ok) {
      saveStatus.textContent = "✓ Case saved successfully.";
      saveStatus.className = "save-status save-ok";
      saveStatus.classList.remove("hidden");
      loadCases();
      setTimeout(() => saveStatus.classList.add("hidden"), 3000);
    } else {
      throw new Error("Save failed");
    }
  } catch {
    saveStatus.textContent = "✗ Save failed. Check server logs.";
    saveStatus.className = "save-status save-err";
    saveStatus.classList.remove("hidden");
  }
}

// ── Saved cases list ───────────────────────────────────────────
async function loadCases() {
  try {
    const res = await fetch("/api/cases");
    const data = await res.json();
    renderCasesList(data.cases || []);
  } catch {}
}

function renderCasesList(cases) {
  const container = document.getElementById("cases-list");
  if (cases.length === 0) {
    container.innerHTML = '<div class="empty-state">No saved cases yet.</div>';
    return;
  }
  container.innerHTML = cases.map(c => {
    const tags = JSON.parse(c.tags || "[]");
    const tagStr = tags.length ? tags.slice(0, 2).join(", ") : "";
    const labelHtml = c.label ? `<span class="case-label-tag">${escapeHtml(c.label)}</span>` : "";
    return `
      <div class="case-item" data-address="${c.address}" data-chain="${c.chain}">
        <div>
          <div class="case-addr">${truncate(c.address, 18)} · ${c.chain}</div>
          ${labelHtml}
          ${tagStr ? `<div class="case-meta">${escapeHtml(tagStr)}</div>` : ""}
          <div class="case-meta">${c.updated_at ? c.updated_at.split("T")[0] : ""}</div>
        </div>
        <button class="case-del" data-id="${c.id}" title="Delete case">✕</button>
      </div>`;
  }).join("");

  // Click to load a case
  container.querySelectorAll(".case-item").forEach(item => {
    item.addEventListener("click", (e) => {
      if (e.target.classList.contains("case-del")) return;
      walletInput.value = item.dataset.address;
      chainSelect.value = item.dataset.chain;
      runAnalysis();
    });
  });

  // Delete buttons
  container.querySelectorAll(".case-del").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id = btn.dataset.id;
      if (!confirm("Delete this case?")) return;
      await fetch(`/api/cases/${id}`, { method: "DELETE" });
      loadCases();
    });
  });
}

// ══ EXPORT ══════════════════════════════════════════════════════
function exportJson() {
  if (!currentResult) return;
  const label  = document.getElementById("case-label").value.trim();
  const notes  = document.getElementById("case-notes").value.trim();
  const tagsRaw= document.getElementById("case-tags").value.trim();
  const tags   = tagsRaw ? tagsRaw.split(",").map(t => t.trim()) : [];

  const report = {
    export_info: {
      tool: "BlueLock Crypto Intel Dashboard",
      version: "1.0.0",
      disclaimer: "Public-chain observational data only. Requires manual verification. Not legal evidence.",
      exported_at: new Date().toISOString(),
    },
    case: {
      address: currentResult.address,
      chain: currentResult.chain,
      analyst_label: label,
      tags,
      notes,
    },
    summary: currentResult.summary,
    risk_observations: currentResult.risk_notes,
    transactions_count: (currentResult.transactions || []).length,
    transactions: (currentResult.transactions || []).slice(0, 100),
    graph: {
      nodes: currentResult.graph_nodes,
      edges: currentResult.graph_edges,
    },
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `bluelock_${currentResult.chain}_${currentResult.address.slice(0, 10)}_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ══ SETTINGS MODAL ══════════════════════════════════════════════
function openSettings() {
  document.getElementById("settings-modal").classList.remove("hidden");
}
function closeSettings() {
  document.getElementById("settings-modal").classList.add("hidden");
}

// ══ ALERTS ══════════════════════════════════════════════════════
function showError(msg) {
  errorBanner.textContent = `⛔ ${msg}`;
  errorBanner.classList.remove("hidden");
}
function showWarning(msg) {
  warningBanner.textContent = `⚠ ${msg}`;
  warningBanner.classList.remove("hidden");
}
function hideAlerts() {
  errorBanner.classList.add("hidden");
  warningBanner.classList.add("hidden");
}

// ══ UTILITIES ════════════════════════════════════════════════════
function truncate(str, n) {
  if (!str) return "";
  if (str.length <= n) return str;
  return str.slice(0, Math.floor(n / 2)) + "…" + str.slice(-Math.floor(n / 3));
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function chainNameFor(chain) {
  const names = {
    ethereum: "Ethereum", bsc: "BNB Chain",
    polygon: "Polygon", arbitrum: "Arbitrum", base: "Base",
  };
  return names[chain] || chain;
}

function getExplorerBase(chain) {
  const bases = {
    ethereum: "https://etherscan.io",
    bsc:      "https://bscscan.com",
    polygon:  "https://polygonscan.com",
    arbitrum: "https://arbiscan.io",
    base:     "https://basescan.org",
  };
  return bases[chain] || "https://etherscan.io";
}
