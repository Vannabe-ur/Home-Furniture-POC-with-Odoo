# Odoo 19 on Docker — New Teammate Onboarding Guide

Welcome to the team! This guide will get you from zero to a running Odoo 19 instance on Docker, then walk you through everything you need to start learning to become an Odoo technical engineer.

---

## Part 1: Prerequisites

Before you start, make sure you have:

- **Docker Desktop** (Mac/Windows) or **Docker Engine + Docker Compose** (Linux) installed
  - Verify with: `docker --version` and `docker compose version`
- **Git** installed (`git --version`)
- A code editor — **VS Code** recommended, with the **Python** and **Odoo Snippets** extensions
- Basic comfort with the terminal/command line
- At least 8GB RAM free and ~10GB disk space

---

## Part 2: Spin Up Odoo 19 with Docker Compose

### Step 1 — Create a project folder

```bash
mkdir odoo19-dev && cd odoo19-dev
mkdir addons
```

The `addons` folder is where you'll put custom/third-party modules later — it gets mounted into the container.

### Step 2 — Create `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16
    container_name: odoo19-db
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      POSTGRES_DB: postgres
    volumes:
      - odoo19-db-data:/var/lib/postgresql/data
    restart: unless-stopped

  odoo:
    image: odoo:19
    container_name: odoo19-app
    depends_on:
      - db
    ports:
      - "8069:8069"
    environment:
      HOST: db
      USER: odoo
      PASSWORD: odoo
    volumes:
      - odoo19-web-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
      - ./config:/etc/odoo
    restart: unless-stopped

volumes:
  odoo19-db-data:
  odoo19-web-data:
```

### Step 3 — Create a config file (optional but recommended)

```bash
mkdir config
```

Create `config/odoo.conf`:

```ini
[options]
addons_path = /mnt/extra-addons
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
```

### Step 4 — Launch it

```bash
docker compose up -d
```

Check the logs to confirm it's healthy:

```bash
docker compose logs -f odoo
```

Wait for a line like `odoo.service.server: HTTP service (werkzeug) running`.

### Step 5 — Open Odoo

Visit **http://localhost:8069** in your browser.

- Create your first database (choose a name like `dev`)
- Set an admin email/password
- Optionally check "Load demo data" — **do this** for a learning environment; demo data gives you sample customers, products, invoices, etc. to explore

### Useful Docker commands to know

| Task | Command |
|---|---|
| Stop everything | `docker compose stop` |
| Start again | `docker compose start` |
| Restart just Odoo (after code changes) | `docker compose restart odoo` |
| Tear down (keep data) | `docker compose down` |
| Tear down + wipe data | `docker compose down -v` |
| Open a shell inside the Odoo container | `docker compose exec odoo bash` |
| Access Odoo's Python shell | `docker compose exec odoo odoo shell -d dev` |
| Access Postgres directly | `docker compose exec db psql -U odoo` |

---

## Part 3: Explore Odoo as a User First

Before touching code, spend a day or two clicking around as a functional user. Understanding the *product* is what makes the *technical* work make sense later.

1. **Enable developer mode**: Settings → scroll to bottom → Activate the developer mode
2. Install a few core apps: **Sales, Inventory, Accounting, CRM**
3. Create a customer, a product, a sales order, confirm it, and watch it flow into a delivery and an invoice
4. Note how apps interconnect (a Sales Order creates a Delivery + Invoice automatically)
5. Look at **Settings → Technical** menu (only visible in dev mode) — this exposes Actions, Views, Fields, Automations, etc. This is your future toolbox.

---

## Part 4: The Odoo Technical Engineer Learning Path

Below is a structured curriculum. Work through it roughly in order — each stage builds on the last.

### Stage 1 — Architecture Fundamentals
- **MVC-ish structure**: Models (Python/ORM) → Views (XML) → Controllers (web/HTTP)
- **Modules**: everything in Odoo is a module (addon) with a defined folder structure
- **The ORM**: Odoo doesn't use raw SQL for business logic — learn `orm.Model`, `fields`, `api.depends`, `api.model`
- **Database**: one Postgres DB per Odoo "database"; each module adds tables via ORM models

📚 Read: Odoo official docs → *Developer Tutorials* section (odoo.com/documentation, pick the 19.0 version)

### Stage 2 — Build Your First Module
Create a minimal custom module inside your `addons/` folder:

```
addons/my_first_module/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── my_model.py
├── views/
│   └── my_model_views.xml
└── security/
    └── ir.model.access.csv
```

Learn to write:
- `__manifest__.py` — module metadata, dependencies, data files
- A simple model with `_name`, `_description`, and a few `fields.Char`, `fields.Many2one`
- A basic list/form view in XML
- An access rights CSV entry (without this, nobody can read/write your model)

Install it via **Apps → Update Apps List → search your module → Install** (make sure "Update Apps List" runs in dev mode after adding a new module folder).

### Stage 3 — Core ORM Concepts
- `@api.depends` computed fields
- `@api.onchange` for live UI feedback
- `search()`, `browse()`, `create()`, `write()`, `unlink()`
- Recordsets and their "list-like" nature (`self` can be 0, 1, or many records)
- `related` fields, `store=True` vs computed-on-the-fly
- Inheritance: `_inherit` (extend existing models) vs `_inherit` + `_name` (new model based on old)

### Stage 4 — Views & UI
- List (tree), form, kanban, calendar, pivot, graph views
- XML inheritance with `xpath` to modify existing views without touching core code
- Widgets (`many2one`, `many2many_tags`, `statusbar`, etc.)
- QWeb basics — Odoo's templating engine, used for both web pages and PDF reports

### Stage 5 — Security
- `ir.model.access.csv` (model-level CRUD permissions)
- Record rules (`ir.rule`) for row-level security
- Groups and `res.groups`

### Stage 6 — Business Logic & Automation
- Server actions and automated actions (`base_automation`)
- Workflows via state fields + buttons (`fields.Selection` + `_compute` + manual triggers)
- Scheduled actions (`ir.cron`)

### Stage 7 — Reports & QWeb
- PDF report templates with QWeb
- `report.template` and paper formats

### Stage 8 — Web Controllers & APIs
- HTTP controllers with `@http.route`
- JSON-RPC / XML-RPC external API access
- REST-style integrations (common in real client work)

### Stage 9 — Testing & Debugging
- `odoo shell` for interactive debugging
- Python unit tests (`TransactionCase`)
- Reading logs: `docker compose logs -f odoo`
- Using `--dev=all` (auto-reload + qweb reload + assets in dev) — add to `odoo.conf` or as a CLI flag for daily dev work

### Stage 10 — Real-World Practices
- Module versioning and dependencies
- Data migration scripts between Odoo versions
- Performance: avoid N+1 queries, use `read_group`, batch operations
- Git workflow for Odoo projects, code review norms
- Odoo Enterprise vs Community differences (if your team touches Enterprise features)

---

## Part 5: Suggested First 2 Weeks

| Day | Focus |
|---|---|
| 1 | Docker setup (this guide), explore Odoo as a user |
| 2 | Developer mode, Technical menu, read module structure of a couple of installed apps |
| 3–4 | Build "Stage 2" first module end-to-end |
| 5 | ORM deep dive — compute fields, onchange, relations |
| 6–7 | Views: list/form/kanban + view inheritance via xpath |
| 8 | Security: access rights + record rules |
| 9 | Automated actions + cron jobs |
| 10 | Pick a small real ticket (with mentor support) and ship it |

---

## Part 6: Handy References

- Official docs: https://www.odoo.com/documentation/19.0/
- Developer tutorials: https://www.odoo.com/documentation/19.0/developer/tutorials.html
- ORM API reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
- OCA (Odoo Community Association) modules on GitHub — great source of real-world code to read

---

## Notes

- The docker-compose setup above uses default `odoo`/`odoo` credentials for Postgres, fine for local dev — **never use these in production**.
- If port 8069 is already taken on your machine, change the left side of `"8069:8069"` in docker-compose.yml, e.g. `"8070:8069"`.
- Whenever you add a new custom module folder, you must go to **Apps → Update Apps List** in the UI (with developer mode on) before it shows up as installable.
