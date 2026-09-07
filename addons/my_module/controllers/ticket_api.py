from odoo import http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request


class ClientTicketApi(http.Controller):
    """Authenticated JSON API for client.ticket records."""

    @staticmethod
    def _ticket_to_dict(ticket):
        return {
            'id': ticket.id,
            'ticket_ref': ticket.ticket_ref,
            'state': ticket.state,
            'priority': ticket.priority,
            'partner_id': ticket.partner_id.id,
            'partner_name': ticket.partner_id.name,
            'request_type': ticket.request_type,
            'product_type': ticket.product_type,
            'requester_id': ticket.requester_id.id,
            'design_manager_id': ticket.design_manager_id.id,
            'designer_id': ticket.designer_id.id,
            'require_date': ticket.require_date.isoformat()
            if ticket.require_date else None,
            'description': ticket.description,
        }

    @http.route(
        '/api/v1/tickets',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def list_tickets(self, **params):
        """Return tickets visible to the logged-in user."""
        domain = []
        if params.get('state'):
            domain.append(('state', '=', params['state']))

        try:
            limit = min(int(params.get('limit', 50)), 100)
        except (TypeError, ValueError):
            limit = 50

        tickets = request.env['client.ticket'].search(
            domain,
            limit=max(limit, 1),
            order='id desc',
        )
        return request.make_json_response({
            'count': len(tickets),
            'data': [self._ticket_to_dict(ticket) for ticket in tickets],
        })

    @http.route(
        '/api/v1/tickets/<int:ticket_id>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_ticket(self, ticket_id, **kwargs):
        ticket = request.env['client.ticket'].browse(ticket_id).exists()
        if not ticket:
            return request.make_json_response(
                {'error': 'Ticket not found'}, status=404
            )
        return request.make_json_response({
            'data': self._ticket_to_dict(ticket),
        })

    @http.route(
        '/api/v1/tickets/<int:ticket_id>',
        type='http',
        auth='user',
        methods=['PUT', 'PATCH'],
        csrf=False,
    )
    def update_ticket(self, ticket_id, **kwargs):
        """Update a ticket while it is still in draft."""
        ticket = request.env['client.ticket'].browse(ticket_id).exists()
        if not ticket:
            return request.make_json_response(
                {'error': 'Ticket not found'}, status=404
            )

        if ticket.state != 'draft':
            return request.make_json_response(
                {'error': 'Only draft tickets can be edited'}, status=400
            )

        payload = request.httprequest.get_json(silent=True) or {}
        allowed_fields = {
            'request_type', 'product_type', 'phone', 'email', 'project_id',
            'design_manager_id', 'designer_id', 'require_date', 'description',
            'phis_ref', 'aihouse_ref', 'priority',
        }
        values = {
            key: value for key, value in payload.items()
            if key in allowed_fields
        }

        raw_partner_id = payload.get('partner_id')
        partner_name = payload.get('partner_name')
        partner_email = payload.get('partner_email')

        if raw_partner_id and str(raw_partner_id).isdigit():
            values['partner_id'] = int(raw_partner_id)
        elif raw_partner_id and not partner_name:
            partner_name = str(raw_partner_id)

        if partner_name:
            partner = request.env['res.partner'].search(
                [('name', '=', partner_name)], limit=1
            )
            if not partner:
                partner = request.env['res.partner'].create({
                    'name': partner_name,
                    'email': partner_email,
                })
            values['partner_id'] = partner.id

        if values.get('partner_id'):
            partner = request.env['res.partner'].browse(
                values['partner_id']
            ).exists()
            if partner:
                values.setdefault('email', partner.email)
                values.setdefault('phone', partner.phone)

        if not values:
            return request.make_json_response(
                {'error': 'No editable fields supplied'}, status=400
            )

        try:
            ticket.write(values)
        except (AccessError, ValidationError) as error:
            return request.make_json_response(
                {'error': str(error)}, status=400
            )

        return request.make_json_response({
            'data': self._ticket_to_dict(ticket),
        })

    @http.route(
        '/api/v1/tickets',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def create_ticket(self, **kwargs):
        payload = request.httprequest.get_json(silent=True) or {}
        allowed_fields = {
            'request_type', 
            'product_type', 
            'phone', 
            'email',
            'project_id', 
            'design_manager_id',
            'require_date',
            'description', 
            'phis_ref', 
            'aihouse_ref',
            'priority',
        }
        values = {
            key: value for key, value in payload.items()
            if key in allowed_fields
        }

        # Accept either a partner ID or a customer name. If the name does
        # not exist, create a partner using the normal Odoo permissions.
        raw_partner_id = payload.get('partner_id')
        partner_name = payload.get('partner_name')
        partner_email = payload.get('partner_email')

        if raw_partner_id and str(raw_partner_id).isdigit():
            values['partner_id'] = int(raw_partner_id)
        elif raw_partner_id and not partner_name:
            partner_name = str(raw_partner_id)

        if not values.get('partner_id'):
            if not partner_name:
                return request.make_json_response(
                    {'error': 'partner_id or partner_name is required'},
                    status=400,
                )

            partner_domain = [('name', '=', partner_name)]
            if partner_email:
                partner_domain = [
                    '|',
                    ('email', '=', partner_email),
                    ('name', '=', partner_name),
                ]

            partner = request.env['res.partner'].search(
                partner_domain,
                limit=1,
            )
            if not partner:
                partner = request.env['res.partner'].create({
                    'name': partner_name,
                    'email': partner_email,
                })
            values['partner_id'] = partner.id

        if values.get('partner_id'):
            partner = request.env['res.partner'].browse(
                values['partner_id']
            ).exists()
            if partner:
                values.setdefault('email', partner.email)
                values.setdefault('phone', partner.phone)

        values['requester_id'] = request.env.user.id

        try:
            ticket = request.env['client.ticket'].create(values)
        except (AccessError, ValidationError) as error:
            return request.make_json_response(
                {'error': str(error)}, status=400
            )

        return request.make_json_response(
            {'data': self._ticket_to_dict(ticket)}, status=201
        )

    @http.route(
        '/api/v1/tickets/<int:ticket_id>/submit',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def submit_ticket(self, ticket_id, **kwargs):
        ticket = request.env['client.ticket'].browse(ticket_id).exists()
        if not ticket:
            return request.make_json_response(
                {'error': 'Ticket not found'}, status=404
            )

        try:
            ticket.action_submitted()
        except (AccessError, ValidationError) as error:
            return request.make_json_response(
                {'error': str(error)}, status=400
            )

        return request.make_json_response({
            'data': self._ticket_to_dict(ticket),
        })
