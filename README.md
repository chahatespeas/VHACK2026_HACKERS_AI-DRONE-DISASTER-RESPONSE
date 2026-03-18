# ai-disaster-simulation

**1. Create and activate a virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt

**3. Run the drone_api**
uvicorn drone_api:app --port 8001

**4. Run the agentWStreamlit (main agent ui)**
_run in separate terminal, not in the same terminal where u did step 3_
streamlit run agentWStreamlit.py

