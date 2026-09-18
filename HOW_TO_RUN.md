# 🚀 How to Run the n8n Workflow Popularity System
Quick instructions to set up, run, and test the project locally on **Windows, macOS, or Linux**, including fixes for common environment and port issues.

---

## ⚡ 1-Minute Quick Start

### 🪟 On Windows (Easiest)

#### Option 1: Instant Launch (Recommended)
Simply double-click:
```cmd
START_API.bat
```
*(Or run `.\START_API.bat` from PowerShell / Command Prompt).*
This automatically verifies dependencies and launches the REST API server.

#### Option 2: Full Setup with Test Suite & Data Pipeline
```cmd
.\SETUP_AND_RUN.bat
```
This runs the full onboarding: verifies Python, installs packages, executes the 17 automated smoke tests, and starts the API.

---

### 🍎 On macOS / 🐧 On Linux

Open your terminal in the project directory:
```bash
chmod +x start_api.sh setup_and_run.sh
./start_api.sh
```
*(Or run `./setup_and_run.sh` to install dependencies and run tests first).*

---

### 💻 Manual Cross-Platform Setup (Terminal / Shell)

1. **Open your terminal** in the root directory:
   ```bash
   cd n8n-workflow-popularity-system
   ```

2. **Create & activate a virtual environment (optional but recommended):**
   ```bash
   # On Windows:
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify tests:**
   ```bash
   python run_tests.py
   ```
   *(Expected output: `17 passed, 0 failed`)*

5. **Start the REST API server:**
   ```bash
   python run_api.py
   ```

---

## 🌐 How to Verify It Is Working

Once started, open your web browser:

| Interface | URL | What You See |
| :--- | :--- | :--- |
| **Interactive Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Test every endpoint interactively directly in your browser. |
| **Live Visual Dashboard** | [http://localhost:8000/dashboard](http://localhost:8000/dashboard) | Visual table showing top workflows, metrics, and charts. |
| **Top 10 Workflows (JSON)** | [http://localhost:8000/workflows/top?limit=10](http://localhost:8000/workflows/top?limit=10) | Top workflows ranked by calculated popularity score. |
| **US-Specific Workflows** | [http://localhost:8000/workflows?country=US](http://localhost:8000/workflows?country=US) | Workflows segmented for United States. |
| **India-Specific Workflows** | [http://localhost:8000/workflows?country=IN](http://localhost:8000/workflows?country=IN) | Workflows segmented for India. |
| **Global Community Topics** | [http://localhost:8000/workflows?country=GLOBAL](http://localhost:8000/workflows?country=GLOBAL) | Discourse forum community threads. |

---

## 🛠️ Troubleshooting & Common Errors Solved

### Issue 1: `python` or `pip` is not recognized
* **Symptom:** `'python' is not recognized as an internal or external command, operable program or batch file.`
* **Cause:** Python is not added to your system's PATH environment variable.
* **Solution:**
  1. Try typing `py` or `python3` instead of `python`:
     ```cmd
     py run_api.py
     ```
  2. Or install Python 3.10+ from [python.org](https://www.python.org/downloads/) and **ensure you check the box: "Add Python to PATH"** during installation.

---

### Issue 2: Port 8000 already in use
* **Symptom:** Another service (or previously launched instance) is occupying port 8000.
* **Built-in Auto-Fix:** `run_api.py` includes automatic conflict resolution. If port 8000 is occupied, it automatically shifts to port **8001** and notifies you on the console.
* **Manual Custom Port:** You can also pass any free port as an argument:
  ```bash
  python run_api.py 8080
  # Opens on http://localhost:8080/docs
  ```

---

### Issue 3: PowerShell Script Execution Policy Error
* **Symptom:** `File ...\activate.ps1 cannot be loaded because running scripts is disabled on this system.`
* **Solution:** Run this command in PowerShell to temporarily permit script execution for your session:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
  Or simply use standard Command Prompt (`cmd.exe`) or double-click `START_API.bat`.

---

### Issue 4: `Permission denied: ./start_api.sh` on macOS / Linux
* **Symptom:** `bash: ./start_api.sh: Permission denied`
* **Solution:** Give execution permissions to the shell scripts:
  ```bash
  chmod +x start_api.sh setup_and_run.sh
  ./start_api.sh
  ```

---

### Issue 5: Missing dependencies (`ModuleNotFoundError`)
* **Symptom:** `ModuleNotFoundError: No module named 'fastapi'`
* **Solution:** Run pip install to install all required libraries:
  ```bash
  pip install -r requirements.txt
  ```

---

### Issue 6: Running `POST /workflows/refresh` without API keys or behind rate limits
* **Symptom:** Calling `/workflows/refresh` returns `"pipeline_mode": "OFFLINE_RESILIENCE_SEED"`.
* **How it works:**
  - When running without a configured YouTube API key or when external rate limits (HTTP 429) are active, the pipeline falls back to the built-in offline seed baseline so tests and scripts complete without crashing.
  - The SQLite database (`data/workflows.db`) is already populated with **1,357 verified records** collected from live endpoints.

---

## 🔄 Optional: Importing Native n8n Workflows (`n8n/*.json`)

If you run an n8n instance locally (`http://localhost:5678`) or via Docker Compose:
1. In your n8n workspace, create an n8n **Data Table** named `workflow_popularity`.
2. Open any workflow JSON from the [`n8n/`](n8n/) folder:
   - `youtube_collector.json`
   - `forum_collector.json`
   - `trends_collector.json`
   - `combine_and_rank.json`
3. In n8n, click **Workflow Menu (top right) → Import from File...**
4. Open the Data Table nodes and select your created table from the dropdown.
5. Click **Test step** or **Execute Workflow** to run live on the n8n canvas!
