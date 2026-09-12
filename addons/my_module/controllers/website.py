from odoo import http
from odoo.http import request


class FurnitureWebsite(http.Controller):
    """Public storefront for the home-furniture business."""

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def home(self, **kwargs):
        return request.render('my_module.furniture_homepage', {
            'website': request.website,
        })

    @http.route(['/products', '/product'], type='http', auth='public', website=True, sitemap=True)
    def products(self, **kwargs):
        return request.render('my_module.furniture_products', {'website': request.website})

    @http.route('/services', type='http', auth='public', website=True, sitemap=True)
    def services(self, **kwargs):
        return request.render('my_module.furniture_services', {'website': request.website})

    @http.route('/about-us', type='http', auth='public', website=True, sitemap=True)
    def about_us(self, **kwargs):
        return request.render('my_module.furniture_about_us', {'website': request.website})
