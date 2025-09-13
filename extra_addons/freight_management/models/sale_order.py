from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    freight_quotation_id = fields.Many2one(
        'freight.quotation',
        string='Freight Quotation',
        readonly=True,
        help='Freight quotation that generated this sale order'
    )
    
    def action_view_freight_quotation(self):
        """Smart button to view related freight quotation"""
        if not self.freight_quotation_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Freight Quotation',
            'res_model': 'freight.quotation',
            'res_id': self.freight_quotation_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
