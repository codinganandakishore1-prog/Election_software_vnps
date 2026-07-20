"""In-app help and documentation for administrators and viewers."""

from __future__ import annotations

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.theme import apply_saved_theme, inject_theme

SECTIONS: list[tuple[str, str, str]] = [
    ("overview", "Overview", "info"),
    ("architecture", "Architecture", "account_tree"),
    ("roles", "Roles & Login", "badge"),
    ("prerequisites", "Prerequisites", "checklist"),
    ("local_setup", "Local Setup", "computer"),
    ("cloudflare", "Cloudflare Tunnel", "public"),
    ("website_guide", "Website Guide", "language"),
    ("desktop_guide", "Desktop App", "how_to_vote"),
    ("election_day", "Election Day", "event"),
    ("reports_analytics", "Reports & Analytics", "bar_chart"),
    ("production", "Production / Render", "cloud"),
    ("troubleshooting", "Troubleshooting", "build"),
]


def _section_card(title: str, icon: str) -> None:
    with ui.row().classes("items-center q-gutter-sm q-mb-sm"):
        ui.icon(icon, size="sm").classes("text-primary")
        ui.label(title).classes("text-h6 text-weight-bold")


def _step(number: int, title: str, body: str) -> None:
    with ui.element("div").classes("emp-card q-pa-md q-mb-sm w-full"):
        ui.label(f"{number}. {title}").classes("text-subtitle1 text-weight-medium q-mb-xs")
        ui.markdown(body).classes("text-body2 text-grey-8")


def _bullets(items: list[str]) -> None:
    for item in items:
        ui.markdown(f"- {item}").classes("text-body2 text-grey-8")


def _tip(text: str) -> None:
    with ui.element("div").classes(
        "q-pa-sm q-mb-md w-full rounded-borders"
    ).style("background: rgba(241, 125, 50, 0.08); border-left: 3px solid #F17D32"):
        ui.markdown(f"**Tip:** {text}").classes("text-body2")


def _render_overview() -> None:
    _section_card("Election Management Platform", "info")
    ui.markdown(
        """
This platform runs school elections end-to-end:

| Piece | What it does |
|-------|----------------|
| **Website (Election Portal)** | Configure elections, monitor nodes, live results, reports |
| **Backend API** | Single source of truth — auth, sync, votes, WebSockets |
| **Desktop voting nodes** | Cast votes (including offline), then sync to the server |
| **Cloudflare Tunnel** | Free HTTPS public URL so viewers can open results worldwide |

**Typical flow**

```
Create election → Positions → Candidates → Create nodes → Publish
     → Start (Live) → Vote on desktop PCs → Sync → Live Results / Reports
```

Use the tabs above as the operator manual: local setup, Cloudflare Tunnel,
website screens, desktop voting, election-day checklist, and troubleshooting.
        """
    ).classes("text-body2")
    _tip(
        "Start with **Local Setup**, then **Cloudflare Tunnel** if you need a public URL. "
        "Follow **Website Guide** before election day, and **Election Day** on the day itself."
    )


def _render_architecture() -> None:
    _section_card("System layout", "account_tree")
    ui.markdown(
        """
```
Internet / mobile viewers
            ↓
   Cloudflare Tunnel (HTTPS)
            ↓
 Website (NiceGUI :8080)  ←→  Backend API (FastAPI :8000)  ←→  Database
            ↑
 Desktop voting nodes (CustomTkinter) — local queue + sync
```

| Component | Default local URL | Role |
|-----------|-------------------|------|
| Backend API | `http://localhost:8000` | Auth, elections, sync, reports, WebSockets |
| Website | `http://localhost:8080` | Admin & viewer portal |
| Desktop app | Local window | Voting stations |
| API health | `http://localhost:8000/health` | Quick uptime check |

**Election types**

- **Regular election** — school-wide positions (typically up to 8 nodes)
- **House election** — Pallava, Pandya, Chera, Chola (typically 2 nodes per house)

**Offline behaviour**

Desktop nodes keep accepting votes if the network or tunnel drops. Votes sit in a
local queue and upload when the API is reachable again. No vote is lost if the
local queue is intact.
        """
    ).classes("text-body2")


def _render_roles() -> None:
    _section_card("Accounts & permissions", "badge")
    ui.markdown(
        """
### Website roles

| Role | Typical use | Can change election data? |
|------|--------------|---------------------------|
| **Super Administrator** | Full control, settings | Yes |
| **Administrator** | Day-to-day election ops | Yes |
| **Viewer** | Live results / read-only dashboards | No |

### Desktop roles

| Role | Access |
|------|--------|
| **Node Admin** | Admin panel — Node Config, download config, sync diagnostics |
| **Teacher / voter** | Voting screen only |

### Demo logins (local SQLite bootstrap)

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Administrator |
| `superadmin` | `super123` | Super Administrator |
| `viewer` | `viewer123` | Viewer |

Multiple viewers can sign in at once. **Change these passwords before any real election.**

Mobile / tablet browsers are intended for **read-only** live results, not configuration.
        """
    ).classes("text-body2")


def _render_prerequisites() -> None:
    _section_card("What you need before starting", "checklist")
    ui.markdown(
        """
### Software

- **Python 3.11+** (recommended)
- Project dependencies: `pip install -r requirements.txt` from the repo root
- Optional: **Docker** + Docker Compose for a full stack
- Optional: **MySQL 8** for production-like local DB (SQLite works for demos)
- **cloudflared** if you want a public HTTPS URL (see Cloudflare Tunnel tab)

### Hardware / network

- One machine (or server) that can run the **backend + website** all day
- Voting PCs for desktop nodes (Windows / macOS / Linux)
- Stable LAN between voting PCs and the API host when possible
- Outbound internet on the host if using Cloudflare Tunnel

### Accounts

- Cloudflare account (free) for Tunnel
- Admin credentials for the website (demo users above, or create your own)

### Repository layout (useful paths)

| Path | Purpose |
|------|---------|
| `.env.example` | Copy to `.env` and edit |
| `deployment/scripts/start_*.sh` | Start backend / website / desktop |
| `deployment/cloudflare/tunnel.yml.example` | Tunnel config template |
| `deployment/PRODUCTION.md` | Docker / Render notes |
| `docs/` | Full SRS / design docs |
| `docker-compose.yml` | One-command local stack |
        """
    ).classes("text-body2")


def _render_local_setup() -> None:
    _section_card("Run everything on one machine", "computer")
    ui.markdown(
        """
From the **repository root**, with Python dependencies installed and a `.env`
file based on `.env.example`.
        """
    ).classes("text-body2 q-mb-md")

    _step(
        1,
        "Clone / open the project and install deps",
        """
```
cd Election_software_vnps
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
        """,
    )
    _step(
        2,
        "Configure environment",
        """
Copy `.env.example` to `.env`.

**Easiest local demo (SQLite, no MySQL):**

```
DATABASE_URL=sqlite+pysqlite:///./data/election_dev.db
BOOTSTRAP_DATABASE=true
BACKEND_URL=http://localhost:8000
WEBSITE_PORT=8080
CORS_ORIGINS=*
```

Leave `JWT_SECRET` and `WEBSITE_STORAGE_SECRET` as long random strings before production.
        """,
    )
    _step(
        3,
        "Start the backend API",
        """
```
bash deployment/scripts/start_backend.sh
```

Confirm: open `http://localhost:8000/health` — you should see a healthy response.
API docs (if enabled): `http://localhost:8000/docs`.
        """,
    )
    _step(
        4,
        "Start the website",
        """
In a **second** terminal (venv activated):

```
bash deployment/scripts/start_website.sh
```

Open `http://localhost:8080` → sign in with `admin` / `admin123`.
        """,
    )
    _step(
        5,
        "Start a desktop voting node (optional)",
        """
In a **third** terminal:

```
bash deployment/scripts/start_desktop.sh
```

Create a node on the website first, then enter **Node ID** + **Node Secret**
under Admin → Node Config in the desktop app.
        """,
    )
    _step(
        6,
        "Docker alternative (all-in-one)",
        """
```
docker compose up --build
```

- API: `http://localhost:8000`
- Website: `http://localhost:8080`

Use this when you want MySQL + API + website without installing them separately.
        """,
    )
    _tip(
        "Always start **backend before website**. For public access, keep both running, "
        "then start Cloudflare Tunnel (next tab)."
    )


def _render_cloudflare() -> None:
    _section_card("Expose the website with Cloudflare Tunnel", "public")
    ui.markdown(
        """
Cloudflare Tunnel gives you **HTTPS** and a public URL **without opening router ports**.
This is the recommended free path until you attach a custom domain.

**You need:** backend + website already running, and a free
[Cloudflare](https://dash.cloudflare.com/) account.
        """
    ).classes("text-body2 q-mb-md")

    _tip(
        "For a quick demo, jump to step 5 (**Quick temporary URL**). Use the named tunnel "
        "steps when you want a stable URL or custom domain."
    )

    _step(
        1,
        "Install cloudflared",
        """
**macOS (Homebrew):**
```
brew install cloudflared
```

**Windows (winget):**
```
winget install Cloudflare.cloudflared
```

Or download the installer from Cloudflare’s *cloudflared* releases.

**Ubuntu / Debian:**
```
curl -L --output cloudflared.deb \\
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

Check: `cloudflared --version`
        """,
    )
    _step(
        2,
        "Log in to Cloudflare",
        """
```
cloudflared tunnel login
```

A browser opens — approve access for your Cloudflare account. Credentials are
stored under `~/.cloudflared/`.
        """,
    )
    _step(
        3,
        "Create a named tunnel",
        """
```
cloudflared tunnel create election-ccu
```

Note the **Tunnel ID** and credentials path
(usually `~/.cloudflared/<tunnel-id>.json`).
        """,
    )
    _step(
        4,
        "Configure ingress (website on port 8080)",
        """
Copy the repo template:

`deployment/cloudflare/tunnel.yml.example` → `~/.cloudflared/config.yml`

Edit it:

```
tunnel: <your-tunnel-id>
credentials-file: /Users/YOU/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: election.yourdomain.com
    service: http://localhost:8080
  # Optional — only if desktop nodes must reach the API over the public internet:
  # - hostname: api.election.yourdomain.com
  #   service: http://localhost:8000
  - service: http_status:404
```

Usually you only expose the **website**. Voting PCs on the same LAN can use
`http://<server-lan-ip>:8000` for the API.
        """,
    )
    _step(
        5,
        "Start the tunnel",
        """
**A) Quick temporary URL (demos — no config file):**
```
cloudflared tunnel --url http://localhost:8080
```

Cloudflare prints something like:
`https://random-words.trycloudflare.com`

Share that URL with viewers. It changes each time you restart quick mode.

**B) Named tunnel (persistent):**
```
cloudflared tunnel run election-ccu
```

Or:
```
cloudflared tunnel --config ~/.cloudflared/config.yml run
```
        """,
    )
    _step(
        6,
        "Custom domain DNS (named tunnel)",
        """
In Cloudflare Zero Trust → Networks → Tunnels → your tunnel → **Public Hostname**,
or run:

```
cloudflared tunnel route dns election-ccu election.yourdomain.com
```

Domain DNS must be managed by Cloudflare.
        """,
    )
    _step(
        7,
        "Update CORS for the public URL",
        """
On the API host, set `CORS_ORIGINS` in `.env` to include the public website origin, e.g.:

```
CORS_ORIGINS=https://random-words.trycloudflare.com,http://localhost:8080
```

or for a custom domain:

```
CORS_ORIGINS=https://election.yourdomain.com,http://localhost:8080
```

Restart the backend after changing `.env`.
        """,
    )
    _step(
        8,
        "Verify end-to-end",
        """
1. Backend health: `http://localhost:8000/health`
2. Local website: `http://localhost:8080`
3. Public URL from cloudflared loads the **login** page over HTTPS
4. Sign in as admin → Dashboard shows WebSocket **Connected**
5. Open Live Results in a second browser / phone on cellular data
        """,
    )
    _step(
        9,
        "Day-of tunnel checklist",
        """
1. Start DB (if MySQL) → backend → website → **then** tunnel
2. Confirm the HTTPS URL loads login
3. Do not close the `cloudflared` terminal
4. If the tunnel drops, restart `cloudflared` — desktop nodes keep voting offline
5. Design target: about **2–5 concurrent viewers** on the public site
        """,
    )


def _render_website_guide() -> None:
    _section_card("Step-by-step: configure an election on the website", "language")
    ui.markdown(
        "Do these **before** voting starts. Only Administrators / Super Administrators "
        "can create and change election data. Viewers skip to Live Results / Dashboard."
    ).classes("text-body2 q-mb-md")

    _step(
        1,
        "Sign in",
        """
Open the website (`http://localhost:8080` or your tunnel URL) → enter username / password.

Use an **Administrator** or **Super Administrator** account for setup.
        """,
    )
    _step(
        2,
        "Create the election — Election Management",
        """
Sidebar → **Election Management** → **Create Election**.

Set name, dates, and keep status **Draft** while you finish positions and candidates.
        """,
    )
    _step(
        3,
        "Define positions — Positions",
        """
Sidebar → **Positions**.

1. Select the election
2. Choose **Regular** or **House**
3. Add positions (name, number of winners, ballot order)
        """,
    )
    _step(
        4,
        "Add candidates — Candidates",
        """
Sidebar → **Candidates**.

Select election and type. Add each candidate with class/section, position,
optional house (house elections), and photo (crop/rotate/preview as needed).
        """,
    )
    _step(
        5,
        "House election extras — House Election",
        """
Sidebar → **House Election** (if you run a house election).

Confirm houses (**Pallava, Pandya, Chera, Chola**), house positions, candidates,
and **node assignments** per house.
        """,
    )
    _step(
        6,
        "Regular election overview — Regular Election",
        """
Sidebar → **Regular Election**.

Review regular positions/candidates and assign **regular voting nodes**.
        """,
    )
    _step(
        7,
        "Create voting nodes & save secrets",
        """
In Regular / House **Node Assignment** (or node creation UI):

1. Create each voting node
2. **Copy Node ID and Node Secret immediately** — the secret is shown once
3. Label which physical PC gets which node

You will paste these into the desktop app (Admin → Node Config).
        """,
    )
    _step(
        8,
        "Theme & branding (optional)",
        """
Sidebar → **Theme & Branding**.

Set school colors / logos used on the portal and configuration packages.
        """,
    )
    _step(
        9,
        "Validate → Publish → Start",
        """
Back in **Election Management** (and validation tabs on Regular / House pages):

1. **Validate** — fix every error listed
2. **Publish** — builds the configuration package nodes will download
3. **Start** — sets status to **Live** so nodes can sync votes

During the day you can **Pause**, **Resume**, or **End** the election from here.
        """,
    )
    _step(
        10,
        "Monitor while live",
        """
| Page | Use |
|------|-----|
| **Dashboard** | Totals, queues, node health, WebSocket status |
| **Node Monitor** | Per-node online / sync status |
| **Live Results** | Tallies for staff and viewers |
| **Analytics** | Charts, rankings, house stats |
| **Audit Logs** | Who changed what |
| **Settings** | System options (admin) |
| **Profile** | Your account |
        """,
    )


def _render_desktop_guide() -> None:
    _section_card("Voting PC (desktop app) workflow", "how_to_vote")
    ui.markdown(
        "Each voting station runs the desktop app. Configure it **after** you create "
        "the node on the website and **after** the election is **Published**."
    ).classes("text-body2 q-mb-md")

    _step(
        1,
        "Install / start the app",
        """
On each voting machine (from the repo, with deps installed):

```
bash deployment/scripts/start_desktop.sh
```

For Windows packaging, use scripts under `deployment/scripts/build_desktop_windows.*`.
        """,
    )
    _step(
        2,
        "Open Admin → Node Config",
        """
Unlock the **Admin** panel with the node admin password, then open **Node Config**.

Enter:

| Field | Example |
|-------|---------|
| API / Website URL | `http://192.168.1.10:8000` (LAN) or public API URL if exposed |
| **Node ID** | From website when the node was created |
| **Node Secret** | Shown once at creation — keep it safe |

Save and confirm the node can authenticate.
        """,
    )
    _step(
        3,
        "Download election configuration",
        """
Use **Download Election** / sync config so the node receives the **published** package.

- Do this **before** students vote
- Do **not** replace config mid-voting
- Election must already be **Published** (and usually **Live** for vote sync)
        """,
    )
    _step(
        4,
        "Run voting",
        """
Teachers use the voting screen to cast ballots.

- Votes are stored **locally first**, then uploaded in the background
- If internet / tunnel / API is down, **voting continues offline**
- Votes sync automatically when connectivity returns
        """,
    )
    _step(
        5,
        "Watch sync health",
        """
In the desktop Admin panel, check queue size and last sync time.

On the website, open **Node Monitor** / **Dashboard** and confirm the node is **Online**.
        """,
    )


def _render_election_day() -> None:
    _section_card("Election-day runbook", "event")
    ui.markdown("Follow this order on the morning of the election.").classes(
        "text-body2 q-mb-md"
    )

    _step(
        1,
        "Morning startup (server)",
        """
1. Power on the host PC / server
2. Start MySQL if used (`docker compose up -d` or local MySQL service)
3. `bash deployment/scripts/start_backend.sh`
4. `bash deployment/scripts/start_website.sh`
5. Start Cloudflare Tunnel (quick or named) if remote viewers need access
6. Open public URL → login page OK
7. Sign in as admin → Dashboard **Connected**
        """,
    )
    _step(
        2,
        "Voting stations",
        """
1. Start desktop app on each PC
2. Confirm Node ID / Secret / API URL
3. Download published config (if not already loaded)
4. Confirm node appears **Online** on Node Monitor
5. Cast a **test vote** on one station and verify it appears on Live Results
6. Clear / reset test data only if your process requires it — otherwise proceed
        """,
    )
    _step(
        3,
        "Go live",
        """
1. Election Management → ensure status is **Live** (Start if still Published)
2. Brief teachers on the voting UI
3. Keep Dashboard / Node Monitor open on an admin laptop
4. Viewers use Live Results via tunnel URL on phones
        """,
    )
    _step(
        4,
        "During voting",
        """
- Watch for offline nodes or growing sync queues
- Pause the election from the website if you need a temporary stop
- Do **not** republish or change candidates/positions mid-vote
- If tunnel drops: restart `cloudflared`; voting PCs keep working offline
        """,
    )
    _step(
        5,
        "Close of day",
        """
1. Confirm all node queues are empty (synced)
2. Election Management → **End** election
3. Generate final reports (Excel / CSV / PDF) from **Reports**
4. Optionally export / back up DB and `backend/generated_reports`
5. Shut down tunnel → website → backend (or leave server up for overnight review)
        """,
    )


def _render_reports_analytics() -> None:
    _section_card("Reports, analytics & audit", "bar_chart")
    _bullets(
        [
            "**Reports** — pick an election, choose Excel / CSV / PDF, click **Generate Report**. "
            "The file downloads and appears in the list (Download / Delete).",
            "You can generate reports while an election is **Live** (snapshot of current results).",
            "**Analytics** — turnout, rankings, house stats, candidate charts, node contribution.",
            "**Audit Logs** — administrator actions for accountability.",
            "Viewers can open live results and dashboards; **generating reports** needs Admin.",
            "Report files are stored under the API `REPORT_FOLDER` (see `.env` / production disk).",
        ]
    )


def _render_production() -> None:
    _section_card("Docker, Render, and production notes", "cloud")
    ui.markdown(
        """
### Docker (production-like local)

```
docker compose up --build
```

| Check | URL |
|-------|-----|
| API health | `http://localhost:8000/health` |
| Storage health | `http://localhost:8000/health/storage` |
| Website | `http://localhost:8080` |

### Render.com (Blueprint)

1. Connect the repo and apply `render.yaml`
2. Set `CORS_ORIGINS` to the public website URL (`https://<service>.onrender.com`)
3. Optionally set `BACKEND_URL` on the website service to the public API URL
4. Keep **election-api at 1 instance** (WebSockets + rate limits are in-process)
5. Uploads/reports persist on the `/data` disk attached to the API
6. Migrations run on API start when `RUN_MIGRATIONS=true`

### Security checklist before a real election

- Change all demo passwords and JWT / storage secrets
- Set `ENVIRONMENT=production` and a strong `JWT_SECRET` (≥ 32 characters)
- Restrict `CORS_ORIGINS` (no `*` in production)
- Prefer named Cloudflare Tunnel + custom domain over quick trycloudflare URLs
- Keep Node Secrets offline; treat them like passwords

More detail: `deployment/PRODUCTION.md`
        """
    ).classes("text-body2")


def _render_troubleshooting() -> None:
    _section_card("Common issues", "build")

    issues = [
        (
            "Website says WebSocket Reconnecting",
            "Hard-refresh the Dashboard (`Cmd+Shift+R` / `Ctrl+Shift+R`). Ensure the "
            "backend is up and you are signed in. Opening a fresh tab reconnects cleanly.",
        ),
        (
            "Cannot log in / invalid token mid-session",
            "Confirm backend is running and `JWT_SECRET` was not rotated. Access tokens "
            "last many hours; the website auto-refreshes. Sign out and back in if needed.",
        ),
        (
            "Report generated but list is empty",
            "Ensure you are on the latest backend (report rows must commit). Hard-refresh "
            "Reports and generate again. Check `REPORT_FOLDER` permissions on the server.",
        ),
        (
            "Desktop votes not appearing on website",
            "Confirm election is **Live**, Node ID/Secret are correct, API URL is reachable "
            "from the PC, and Node Monitor shows the node **Online**. Check the local sync queue.",
        ),
        (
            "Tunnel URL not loading",
            "Confirm the website listens on the port in the tunnel config (`8080`), restart "
            "`cloudflared`, and check the Cloudflare dashboard for tunnel status. "
            "Quick tunnels expire when the process stops.",
        ),
        (
            "CORS / blocked browser requests after going public",
            "Add the exact public origin (including `https://`) to `CORS_ORIGINS` and "
            "restart the backend.",
        ),
        (
            "Node cannot download config",
            "Election must be **Published**. Check API URL, credentials, and that the "
            "config package exists on the server (`CONFIG_PACKAGE_FOLDER`).",
        ),
    ]

    for title, body in issues:
        with ui.element("div").classes("emp-card q-pa-md q-mb-sm w-full"):
            ui.label(title).classes("text-subtitle2 text-weight-medium")
            ui.markdown(body).classes("text-body2")

    with ui.element("div").classes("emp-card q-pa-md w-full"):
        ui.label("Deeper documentation in the repo").classes(
            "text-subtitle2 text-weight-medium"
        )
        ui.markdown(
            """
- `docs/01_Project_Overview_and_Core_Requirements.md`
- `docs/02_Desktop_Voting_Application.md`
- `docs/03_Website_and_Admin.md`
- `docs/04_Backend_Database_API.md`
- `docs/05_Node_Synchronization.md`
- `docs/06_UI_UX_Deployment.md` — Cloudflare Tunnel architecture
- `deployment/PRODUCTION.md` — Docker / Render
- `deployment/cloudflare/tunnel.yml.example`
- `.env.example` — all environment variables
            """
        ).classes("text-body2")


RENDERERS = {
    "overview": _render_overview,
    "architecture": _render_architecture,
    "roles": _render_roles,
    "prerequisites": _render_prerequisites,
    "local_setup": _render_local_setup,
    "cloudflare": _render_cloudflare,
    "website_guide": _render_website_guide,
    "desktop_guide": _render_desktop_guide,
    "election_day": _render_election_day,
    "reports_analytics": _render_reports_analytics,
    "production": _render_production,
    "troubleshooting": _render_troubleshooting,
}


def register_help_routes() -> None:
    """Register the Help / Documentation page."""

    @ui.page("/help")
    @require_auth
    def help_page() -> None:
        inject_theme()
        apply_saved_theme()

        with admin_shell("/help") as content:
            with content:
                with ui.column().classes("gap-0 q-mb-md"):
                    ui.label("Documentation").classes("emp-page-title")
                    ui.label(
                        "Full operator guide — local setup, Cloudflare Tunnel, website, "
                        "desktop voting, and election day."
                    ).classes("emp-page-subtitle")

                tabs = ui.tabs().classes("w-full")
                with tabs:
                    tab_refs = {key: ui.tab(label) for key, label, _ in SECTIONS}

                panels = ui.tab_panels(tabs, value=tab_refs["overview"]).classes(
                    "w-full q-mt-md"
                )
                with panels:
                    for key, _label, _icon in SECTIONS:
                        with ui.tab_panel(tab_refs[key]):
                            with ui.element("div").classes("emp-card q-pa-md w-full"):
                                RENDERERS[key]()
