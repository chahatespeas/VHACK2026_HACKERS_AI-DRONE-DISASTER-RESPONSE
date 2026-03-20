# VHACK2026_HACKERS_AI-DRONE-DISASTER-RESPONSE
Our AI Drone Disaster Response system is armed with the ability to document, detect and deploy drones to the optimal routes in scanning for survivors by using the Model Context Protocol. First responders are the backbone of rescuing victims of calamities — both the expected and unforeseen — but their capabilities are limited and time is essential. We aim aid to in this part of this process, by relieving the rescuers from identifying the victims. Knowing their locations beforehand would allow responders to manage their missions efficiently, ensuring all victims are found. 

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
```

**3. Run the drone_api**
```
uvicorn drone_api:app --port 8001
```

**4. Run the agentWStreamlit (main agent ui)**
```
_run in separate terminal, not in the same terminal where u did step 3_
streamlit run agentWStreamlit.py
```

