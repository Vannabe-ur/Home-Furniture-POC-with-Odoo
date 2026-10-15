{
    'name': 'Design Request',
    'version': '19.0.2.0.0',
    'summary': 'Manage house project decoration requests from clients',
    'category': 'Services',
    'author': 'N. Vanna',
    'depends': ['base', 'mail', 'project', 'mrp', 'account', 'sale', 'sale_management', 'website'],
    'data' : [
        # 1. Security file load first
        'security/design_request_security.xml',
        'security/ir.model.access.csv',

        # 2. Sequence and structural data configuration
        'data/design_request_sequence.xml',
        'data/bill_of_quantity_sequence.xml',
        'data/design_request_projects.xml',
        'data/design_request_product_categories.xml',
        'data/product.template.csv',
        'data/product_landscape_uom.xml',
        'data/design_request_cron.xml',

        # 3. Mail & Communication template
        'data/design_request_mail_templates.xml',
        'data/bill_of_quantity_mail_templates.xml',

        # 4. Core Business Views
        'views/design_request_views_ver2.xml',
        'views/design_request_assign_warning_views.xml',
        'views/bill_of_quantity_views.xml',
        'views/project_views.xml',

        # 5. Inherited standard Views
        'views/account_move_views.xml',
        'views/res_partner_views.xml',

        # 6. Web & Printing Engine outputs
        'report/design_request_report.xml',
        'report/bill_of_quantity_report.xml',
        'views/website_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'my_module/static/src/css/furniture.css',
        ],
    },
    'installable': True,
    'application': True,
}
