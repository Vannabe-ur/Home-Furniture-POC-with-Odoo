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
docker compose exec odoo odoo -d luma -u my_module --stop-after-init && docker compose restart odoo
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

---

## Bill of Quantity (BoQ)

The BoQ is the costing and approval document for a Design Request. It is
linked to one Design Request and carries the customer, required date, Design
Area, responsible designer, Design Manager, budget, attachments, item lines,
version, and revision date.

### BoQ items and costing

Each BoQ item can contain:

- Date
- Job Type: Material, Service, or Labor
- Product
- Description
- Quantity and Unit of Measure
- Sale Price
- Subtotal

The BoQ separates costs into Materials, Service / Overhead, and Labor. The
calculation is:

```text
Base Cost = Materials Cost + Service / Overhead Cost + Labor Cost
Margin Cost = Base Cost × Margin Percentage
Total Estimate Cost = Base Cost + Margin Cost
```

The Billing Summary displays the three cost categories, Margin Cost, and Total
Cost on the right side of the BoQ form and report.

### BoQ workflow

```text
Draft → Submitted → Approved → Done
                 ↘ Rejected → Draft (new version)
```

- **Draft**: the designer prepares or revises the BoQ.
- **Submitted**: the BoQ is sent to the assigned Design Manager.
- **Approved**: the manager approves the submitted version.
- **Done**: the approved BoQ is finalized and can create a Sale Quotation.
- **Rejected**: the manager must provide feedback. The BoQ returns to Draft,
  increments its Version, updates Revision Date, and notifies the designer.
- **Cancelled**: the BoQ is stopped and cannot continue through the normal
  workflow.

The Submit button becomes **Resubmit** when the Version is greater than 1.
Reset to Draft is not available from the BoQ form.

### Audit History

The Audit History tab records workflow and revision events, including creation,
submission, approval, rejection, completion, cancellation, and version
changes. Each entry records the event time, user, state, version, and any
feedback or note.

### Access control

- Administrators can access all BoQs.
- Design Managers can access BoQs linked to Design Requests assigned to them.
- Designers can access BoQs linked to Design Requests assigned to them.
- BoQ lines and Audit History follow the same assignment-based access rules.

### Views and reporting

BoQ provides List, Kanban, Calendar, Pivot, and Form views. The BoQ Summary
report is available from the Print menu and uses a clean, borderless Billing
Summary layout.

### Sale Quotation integration

A Sale Quotation can be created only after the BoQ reaches **Done**. The action:

- Uses the BoQ customer.
- Sets Source Document to the Design Request sequence.
- Links the quotation to the BoQ and Design Request.
- Copies BoQ item lines into Order Lines without Date and Job Type.
- Brings the BoQ base amount, margin percentage, and Total Estimate Cost into
  the quotation summary.

The quotation provides smart buttons back to the related BoQ and Design
Request. The BoQ provides a smart button to its related quotations.

---

## Inventory: Products and Operations

The Inventory part of this project is used as the product master for the
design and quotation workflow. Products are created in Odoo's standard
**Product** model and can then be selected on BoQ lines. The catalog is loaded
from `addons/my_module/data/product.template.csv` when the module is installed
or upgraded.

### Product structure

The catalog contains two practical product types:

| Product type | Odoo configuration | Purpose in this project |
|---|---|---|
| Physical design product | Consumable with inventory tracking enabled | Furniture, fixtures, outdoor items, and other supplied items |
| Service product | Service with inventory tracking disabled | Installation, delivery, modification, measurement, consultation, and blueprint/designer fees |

Physical products are grouped into Interior, Exterior, and Outdoor categories.
Service products are grouped under Design Services / Overhead. Each product has
a product name, internal reference, category, sales price, and internal cost.
The reference follows the catalog format:

```text
[Zone][Area]-[Category]-[Sequence]
```

Examples include `ILR-SFA-001` for an interior living-room sectional sofa,
`EBF-LGT-001` for an exterior facade light, and `SVC-INS-001` for an
installation service.

### Inventory product configuration

The catalog CSV maps directly to Odoo's `product.template` model. The main
configuration columns are:

| CSV field | Inventory meaning | Example |
|---|---|---|
| `name` | Product name shown to users | Upholstered Modular Sectional Sofa |
| `default_code` | Internal Reference / SKU used for searching and identification | `ILR-SFA-001` |
| `type` | Product type: `consu` for physical items or `service` for services | `consu` |
| `is_storable` | Enables inventory quantity tracking for physical products | `1` for physical items, `0` for services |
| `categ_id/id` | Inventory product category | Interior, Exterior, Outdoor, or Design Services / Overhead |
| `uom_id` | Sales and BoQ unit of measure | `Unit(s)` or `m³` |
| `sale_ok` | Allows the product to be used in sales and quotations | `1` |
| `purchase_ok` | Allows the product to be selected for purchasing | `1` for physical products, `0` for services |
| `list_price` | Public sales price and default BoQ sales price | Demo selling price |
| `standard_price` | Internal cost used as the cost reference | Demo internal cost |

The prices in this academic project are demonstration values. They can be
changed from the product form in Inventory without changing the reference-code
system.

### Internal Reference code explained

The internal reference uses three segments and four logical parts:

```text
ZZZ-CCC-NNN
│   │   └── Three-digit sequence number
│   └────── Three-letter product category
└────────── Three-character zone and area code
```

The first character identifies the broad design zone:

| Letter | Zone |
|---|---|
| `I` | Interior |
| `E` | Exterior |
| `O` | Outdoor |

The next two characters identify the design area. The complete three-character
prefix is shown below because some two-letter area codes are reused in another
zone:

| Prefix | Design area |
|---|---|
| `ILR` | Interior / Living Room |
| `IBR` | Interior / Bedroom |
| `IKT` | Interior / Kitchen |
| `IDR` | Interior / Dining Room |
| `IBT` | Interior / Bathroom |
| `IHO` | Interior / Home Office |
| `IEF` | Interior / Entrance / Foyer |
| `EBF` | Exterior / Building Facade |
| `EME` | Exterior / Main Entrance |
| `EBT` | Exterior / Balcony / Terrace |
| `ERT` | Exterior / Rooftop |
| `EEW` | Exterior / Exterior Walls |
| `EPA` | Exterior / Parking Area |
| `OBG` | Outdoor / Backyard / Garden |
| `OSP` | Outdoor / Swimming Pool |
| `OPT` | Outdoor / Patio |
| `OOL` | Outdoor / Outdoor Living Area |
| `OOD` | Outdoor / Outdoor Dining Area |
| `OOK` | Outdoor / Outdoor Kitchen |
| `OLA` | Outdoor / Landscape Area |

For example, `ILR` means **Interior + Living Room**, while `OBG` means
**Outdoor + Backyard / Garden**. The area code is followed by a three-letter
category abbreviation describing the product, such as `SFA` for sectional
sofa, `CHR` for chair, `TAB` for table, `CAB` for cabinet, `LGT` for light,
or `GRL` for grill, `ROC` for decorative rock, `BLD` for boulder, `PLN` for
planter, or `PLT` for plant. The final three digits identify the item sequence within
the catalog, such as `001`, `002`, or `003`. An area abbreviation may be
reused in different zones when the full three-character prefix remains
different; for example, `IBT` is Interior / Bathroom and `EBT` is Exterior /
Balcony / Terrace.

Landscape products use the `OLA` prefix. For example, the catalog includes
`OLA-ROC-003` for decorative natural river pebbles, `OLA-PLN-001` for a
geometric concrete planter, and `OLA-PLT-001` for an architectural bird of
paradise plant. All of these products are physical consumables in the Outdoor
inventory category and can be selected on BoQ lines for Landscape Area designs.

Landscape decorative rocks (`OLA-ROC-003` through `OLA-ROC-005`) use the
standard Odoo cubic-metre UoM for both sales and purchasing, so their list and
cost prices are per m³. Boulders, planters, and plants use `Unit(s)` because
they are supplied as individual items.

Service products use the same readable internal-reference idea with the
`SVC` prefix:

| Code | Service |
|---|---|
| `SVC-INS` | Installation |
| `SVC-DLV` | Delivery and placement |
| `SVC-MOD` | Furniture modification |
| `SVC-MSR` | Site measurement |
| `SVC-DSN` | Design consultation |
| `SVC-BLU` | Architectural blueprint and designer service fee |

The code is an internal business identifier, not an Odoo database ID. It helps
users search, classify, quote, and report products consistently across
Inventory, BoQ, Sales, and Invoicing.

### How products are used in operations

The operational flow is:

```text
Product catalog
    -> BoQ line selection
    -> Cost and selling-price calculation
    -> BoQ approval and customer review
    -> Sale quotation
    -> Invoice data from the sale order
```

1. Products are maintained in Inventory or loaded from the module catalog.
   The product's sales price is used as the default BoQ line price when a
   product is selected.

2. A designer selects products on BoQ lines and classifies each line as
   Material, Service / Overhead, or Labor. The selected product supplies the
   description and unit of measure. Quantity multiplied by sale price produces
   the line subtotal.

3. The BoQ calculates material cost, service/overhead cost, labor cost, margin,
   and total estimate cost. A blueprint or design file must be attached before
   the BoQ can be submitted.

4. After manager approval and customer approval, the completed BoQ creates a
   Sale Quotation. The quotation receives the BoQ products as order lines. A
   separate service product named `BOQ-MARGIN` is used for the calculated margin
   when a margin exists.

5. When the quotation is invoiced, the related BoQ reference, margin, and total
   cost are carried into the invoice information provided by this module.

### Inventory scope of this academic project

The current implementation demonstrates product master data, product
categorization, BoQ costing, service charges, quotation creation, and the link
from quotations to invoices. It does not currently implement a complete stock
operations cycle. In particular, it does not automatically create or validate
receipts, delivery orders, stock transfers, purchase orders, manufacturing
orders, or real-time stock replenishment rules.

Therefore, adding a product to the catalog makes it available for selection in
the BoQ and Sales applications; it does not mean that physical stock has been
received or delivered. Those operations would require stock locations,
warehouses, routes, vendors, replenishment rules, and validated inventory
pickings in a later expansion.
