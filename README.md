# Odoo First Module

## Practicing Stage by Stage

### Stage 5 — Security
Odoo uses a multi-layered, group-based security access control system to regulate what users can view, create, edit, or delete.

Odoo enforces access control through four main layers:

- **Users & Groups (RBAC)**: Permissions belong to security groups, not individuals. Users inherit rights via group membership and group inheritance (`implied_ids`).

- **ACLs (Model-Level)**: Grants broad CRUD (Create, Read, Write, Unlink) access per database table via `ir.model.access.csv`.

- **Record Rules (Row-Level)**: Dynamically filters specific records using Python domain expressions (e.g., users only see their own sales leads).

- **Field & UI Security**: Restricts specific fields, buttons, and menu items directly in view XMLs or Python code based on user groups.

In module development files:

1. `security/client_ticket_security.xml` : definee custom security categories and groups.

2. `security/ir.model.access.csv` : define model-level CRUD permissions for each group using `1` (true) or `0` (false).

3. Manifest Declaration: Ensure both security files are registered under the `data` key in `__manifest__.py`.

---

### Stage 6 — Business Logic & Automation

Business logic and automation were implemented through a powerful combination of no-code Automation Rule (Odoo Studio) and backend Python development.

Where Business Logic lives in Odoo code:

- **Python Models:** `models/*.py` — overriding CRUD (create, write, unlink), computed fileds, state changes, action buttons.

- **Security XML:** `security/*.xml` — record rules (`domain_force`), user group capabilities.

- **Automated Actions:** `data/*_cron.xml`/Scheduled Actions — Background jobs like sending ticket reminders, automated currency rate.