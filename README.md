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

---

### Stage 7 — Reports & QWeb

+ **Engine:** Reports are built using standard HTML/QWeb templating and converted into PDF via `wkhtmltopdf`.

+ **Structure:** 

    The report has two primary components:

    1. **Report Action Declaration**
    
    `<record id="action_report_client_ticket" model="ir.actions.report"> ... </record>`

    This block registers the report in Odoo's action framework and binds it to the target model so it appears in the user interface (e.g., under the `Print` menu)
    
    - `id="action_report_client_ticket"` & `model="ir.actions.report"`: Defines a unique identifier for the report action record in Odoo's database.

    - `name`: The user-facing title shown in the UI (**Ticket Summary**).

    - `model` & `binding_model_id`: Links the report to the target record model (client.ticket).

    - `report_type`: Specifies qweb-pdf to tell Odoo to render HTML using QWeb and convert it into a PDF via wkhtmltopdf.

    - `report_name` & `report_file`: Points to the external template ID (`my_module.report_client_ticket_template`) that contains the visual layout.

    - `print_report_name`: Dynamically generates the default file name when downloaded (e.g., Ticket - CT/2026/00001).

    - `binding_type`: Set to report, which embeds this action directly into the Print dropdown on the record view.

    2. **QWeb Report Template**

    `<template id="report_client_ticket_template"> ... </template>`

    This block contains the HTML layout, Bootstrap grid classes, dynamic field evaluations, and CSS styles used to build the page.

    A. Framework Wrappers & Control Loops

    - `web.html_container`: A required top-level wrapper that sets up basic HTML boilerplate, headers, footers, and asset loading.

    - `t-foreach="docs" t-as="doc"`: Iterates over every selected record. docs contains the active recordset, and doc acts as the current record variable.

    - `web.external_layout`: Imports the system's default header and footer layout (company logo, address, page numbers).

    - `<div class="page">`: The main body container. Any content inside this block becomes the core content rendered on the PDF page.

    B. Inline Styling (`<style>`)

    - Contains custom CSS classes used specifically for this report to maintain consistent typography, table formatting, colors (#2f5597 accent color), and spacing.

    C. Section Breakdown

    - Header / Banner (`<div class="row">`): Displays the main title (CLIENT SERVICE TICKET), subtitle, ticket reference (`doc.ticket_ref`), and creation timestamp (`doc.create_date`).

    - Status & Priority Bar: Uses Bootstrap grid layout to align status and priority side by side.

    - Request Details Table (`ticket-table`): A 4-column structured table mapping key field data such as partner_id, request_type, product_type, phone, email, and deadline info.

    - Assignment Table: Displays involved personnel (`requester_id`, `design_manager_id`, `designer_id`, and `bom_id`).

    - Description Box: Uses `<div class="ticket-content">` with CSS `white-space: pre-wrap;` to preserve formatting and line breaks from the text field.

    - References Table: Displays external cross-references (`phis_ref` and `aihouse_ref`). 

---

### Stage 8 — Web Controllers & APIs

- HTTP controllers with `@http.route`

- JSON-RPC / XML-RPC external API access

- REST-style integrations (common in real client work)

**RESTART:**

```
docker compose exec odoo odoo -d odoo-dev -u my_module --stop-after-init && docker compose restart odoo
```

---

## Design Request Project Tasks

When a manager assigns a Design Request, the module creates one task using the
format `Design Request ID - Design Area`.

The task is placed in the Project selected on the request. If no Project is
selected, it automatically uses the Project matching the Request Type:

- Interior Design → Interior Design
- Exterior Design → Exterior Design
- Outdoor Design → Outdoor Design

The selected Project is stored on the request when assignment is completed.
