# ◈ BlueLock Crypto Intel Dashboard

**A defensive, read-only public-chain cryptocurrency forensics dashboard for analysts and investigators.**

> **🔑 API keys are not included and are not provided.**
> You must obtain your own free API keys from each blockchain explorer before the tool will function.
> See [API Key Setup](#-api-key-setup) below for instructions.

---

## ⚠ Legal & Ethical Use Disclaimer

This tool is designed exclusively for:
- Defensive security research
- Public blockchain data analysis
- Educational purposes
- Scam/fraud exposure investigations using public on-chain data

**This tool NEVER:**
- Asks for seed phrases or private keys
- Submits blockchain transactions
- Connects to wallets
- Scrapes private data
- Stores anything beyond your local SQLite database

**All findings are observational only.** Labels, risk notes, and wallet associations are based on publicly available data and require manual verification by a qualified analyst. No finding from this tool constitutes legal evidence or proof of criminal activity.

Use responsibly. Always verify findings independently. Comply with applicable laws in your jurisdiction.

---

## 🚀 Quick Start (Windows 11)

1. **Unzip** the `BlueLock-Crypto-Intel` folder to any location (e.g., your Desktop)
2. **Double-click** `run.bat`
3. The browser will open automatically to `http://127.0.0.1:8000`
4. Enter a wallet address, select a chain, click **Analyze**

> First run takes a minute — it installs Python dependencies automatically.

---

## 🔑 API Key Setup

The dashboard uses free public APIs from blockchain explorers. Without API keys, the app will show a friendly message asking you to add them.

**How to add keys:**

1. Open the `.env` file in your project folder with Notepad
2. Add your keys after the `=` sign:
   ```
   ETHERSCAN_API_KEY=your_key_here
   ```
3. Save the file and restart the server (close the window, double-click `run.bat` again)

**Where to get free API keys:**

| Chain | Site |
|-------|------|
| Ethereum | https://etherscan.io/apis |
| BNB Chain | https://bscscan.com/apis |
| Polygon | https://polygonscan.com/apis |
| Arbitrum | https://arbiscan.io/apis |
| Base | https://basescan.org/apis |

Free tier keys support up to 5 requests/second — sufficient for this tool.

---

## 📁 Project Structure

```
BlueLock-Crypto-Intel/
│
├─ run.bat              ← Double-click to start
├─ install.bat          ← Setup only (no server start)
├─ requirements.txt     ← Python dependencies
├─ .env.example         ← Template for API keys
├─ .env                 ← Your actual keys (auto-created)
│
├─ app/
│  ├─ main.py           ← FastAPI routes
│  ├─ config.py         ← Settings & chain configuration
│  ├─ database.py       ← SQLite operations
│  ├─ models.py         ← Pydantic data models
│  │
│  ├─ services/
│  │  ├─ etherscan_client.py  ← Block explorer API client
│  │  ├─ wallet_profiler.py   ← Parse transactions
│  │  ├─ graph_builder.py     ← Build counterparty graph
│  │  ├─ timeline_builder.py  ← Sort & flag transactions
│  │  ├─ risk_engine.py       ← Heuristic observations
│  │  └─ label_engine.py      ← Known address labels
│  │
│  └─ static/
│     ├─ index.html     ← Dashboard UI
│     ├─ style.css      ← Styling
│     └─ dashboard.js   ← Frontend logic
│
├─ data/
│  ├─ cases.db          ← SQLite database (auto-created)
│  └─ labels.json       ← Custom address labels
│
└─ reports/             ← Exported JSON reports go here
```

---

## 🖥 Dashboard Features

### Wallet Analysis
- Enter any EVM-compatible wallet address (0x...)
- Select chain: Ethereum, Base, BNB Chain, Polygon, or Arbitrum
- Click **Analyze** to fetch and process public on-chain data

### Wallet Summary Card
- Address, chain, transaction count, token transfer count
- First seen / last seen timestamps
- Native token balance (ETH, BNB, MATIC, etc.)

### Analyst Observations (Risk Notes)
Heuristic notes based on observed transaction patterns:
- New / low-activity wallet warning
- High-volume wallet detection
- Many unique counterparties (possible distribution)
- Exchange interaction (possible deposit/withdrawal)
- DEX router interaction (possible swap activity)
- Bridge interaction (possible cross-chain movement)
- Large value movements (≥ 5 native tokens)
- Incoming/outgoing transaction ratio anomalies

> All observations use hedged language: "possible", "observed", "requires verification"

### Counterparty Map
- Interactive graph powered by Cytoscape.js
- Center node = target wallet
- Color-coded by node type: Exchange (purple), DEX (cyan), Bridge (orange), Contract (gray), Wallet (dark blue)
- Node size reflects interaction count
- Click a node to copy address to search field

### Transaction Timeline
- All normal and token transactions, most recent first
- Filter by: All, Incoming, Outgoing, DEX, Flagged
- Large movements highlighted
- Known counterparty labels shown
- Direct link to transaction on block explorer

### Case Notes
- Save analyst label, tags, and investigation notes
- Notes stored locally in SQLite
- Export complete investigation as JSON

---

## 🏷 Custom Address Labels

Add your own labels to `data/labels.json`:

```json
{
  "0xabc123...": ["My Label", "custom"],
  "0xdef456...": ["Suspected Exchange", "exchange"]
}
```

Valid categories: `exchange`, `dex`, `bridge`, `stablecoin`, `defi`, `contract`, `custom`

---

## 🔧 Troubleshooting

**"Python was not found"**
→ Install Python 3.11+ from https://python.org
→ During install, check **"Add Python to PATH"**
→ Restart the command window

**"Failed to create virtual environment"**
→ Make sure Python includes the `venv` module (included by default)
→ Try running `python -m venv .venv` manually in the folder

**"Dependency installation failed"**
→ Check your internet connection
→ Try: `.venv\Scripts\pip install -r requirements.txt`

**"No transactions found" for a valid address**
→ The wallet may be new, have 0 transactions, or be on a chain with no activity
→ Check the address directly on the explorer

**API key errors**
→ Verify the key in your `.env` file has no spaces before/after it
→ Make sure you copied the full key from the explorer
→ Free keys have rate limits — wait a moment and try again

**Graph doesn't appear**
→ Cytoscape.js loads from CDN — requires internet for first load
→ Check browser console for errors (F12 → Console)

**Port 8000 already in use**
→ Another app is using port 8000
→ Edit `run.bat` and change `--port 8000` to `--port 8001`
→ Also change the browser open URL to match

---

## 📸 Screenshot Tips

For investigation thread screenshots:
1. Use Firefox or Chrome in full-screen mode
2. The dark theme is optimized for readability
3. Transaction timeline with "FLAGGED" filter shows most relevant activity
4. Export JSON for detailed evidence documentation
5. Include the "ANALYST OBSERVATIONS" panel in screenshots for context

---

## 🔒 Security & Privacy

- **Local only**: All data stays on your machine
- **No telemetry**: Zero analytics, tracking, or external calls except configured API endpoints
- **No wallet connections**: This tool never asks for MetaMask, WalletConnect, or any wallet integration
- **Read-only**: No transactions are ever submitted to any blockchain
- **SQLite**: Your investigation notes are stored locally in `data/cases.db`

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+ / FastAPI / Uvicorn |
| Database | SQLite via aiosqlite |
| HTTP Client | httpx (async) |
| Frontend | HTML5 / CSS3 / Vanilla JS |
| Graph | Cytoscape.js |
| Config | python-dotenv |

---

*BlueLock Crypto Intel Dashboard — Public chain forensics for analysts and investigators.*
*Read-only. Local-only. No telemetry.*

*Built and maintained by [BlueLock Systems LLC](https://github.com/bluelocksystems-lab)*
