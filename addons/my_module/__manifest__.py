{
    'name': 'My Module',
    'version': '2.0',
    'summary': 'Manage house project decoration requests from clients',
    'category': 'Services',
    'author': 'Vanna',
    'depends': ['base', 'mail', 'project', 'mrp'],
    'data' : [
        'security/client_ticket_security.xml',
        'security/ir.model.access.csv',
        'data/client_ticket_sequence.xml',
        'views/client_ticket_views.xml',
        'views/res_partner_views.xml',
        'data/client_ticket_cron.xml',
    ],
    'installable': True,
    'application': True,
}
