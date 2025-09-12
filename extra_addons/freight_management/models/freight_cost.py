from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class FreightCostLine(models.Model):
    _name = 'freight.cost.line'
    _description = 'Freight Cost Line'
    _order = 'sequence, id'

    shipment_id = fields.Many2one(
        'freight.shipment',
        string='Shipment',
        ondelete='cascade'
    )
    
    quotation_id = fields.Many2one(
        'freight.quotation',
        string='Quotation',
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    cost_type = fields.Selection([
        ('sell', 'Sell Cost (Customer)'),
        ('buy', 'Buy Cost (Vendor)')
    ], string='Cost Type', required=True, default='sell')
    
    cost_category = fields.Selection([
        ('freight', 'Freight Charges'),
        ('documentation', 'Documentation'),
        ('handling', 'Handling Charges'),
        ('insurance', 'Insurance'),
        ('customs', 'Customs Clearance'),
        ('delivery', 'Delivery Charges'),
        ('storage', 'Storage/Demurrage'),
        ('fuel', 'Fuel Surcharge'),
        ('security', 'Security Charges'),
        ('other', 'Other Charges')
    ], string='Cost Category', required=True)
    
    description = fields.Char(
        string='Description',
        required=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor/Customer',
        help='Vendor for buy costs, Customer for sell costs'
    )
    
    quantity = fields.Float(
        string='Quantity',
        default=1.0
    )
    
    unit_price = fields.Monetary(
        string='Unit Price',
        currency_field='currency_id'
    )
    
    amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='shipment_id.currency_id',
        store=True
    )
    
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        readonly=True
    )
    
    invoiced = fields.Boolean(
        string='Invoiced',
        compute='_compute_invoiced',
        store=True
    )

    @api.depends('invoice_line_id')
    def _compute_invoiced(self):
        for line in self:
            line.invoiced = bool(line.invoice_line_id)


class FreightQuotation(models.Model):
    _name = 'freight.quotation'
    _description = 'Freight Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'reference'

    reference = fields.Char(
        string='Quotation Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('is_company', '=', True)],
        tracking=True
    )
    
    # Route Information
    origin_port_id = fields.Many2one(
        'freight.port',
        string='Origin Port',
        required=True
    )
    
    destination_port_id = fields.Many2one(
        'freight.port',
        string='Destination Port',
        required=True
    )
    
    transport_mode = fields.Selection([
        ('air', 'Air Freight'),
        ('ocean', 'Ocean Freight'),
        ('land', 'Land Freight')
    ], string='Transport Mode', required=True)
    
    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], string='Direction', required=True, tracking=True, help='Indicates whether this is an import or export quotation')
    
    service_type = fields.Selection([
        ('fcl', 'Full Container Load (FCL)'),
        ('lcl', 'Less than Container Load (LCL)'),
        ('ftl', 'Full Truck Load (FTL)'),
        ('ltl', 'Less than Truck Load (LTL)'),
        ('air_freight', 'Air Freight'),
        ('express', 'Express Service')
    ], string='Service Type')
    
    # Cargo Information
    cargo_description = fields.Text(
        string='Cargo Description'
    )
    
    estimated_weight = fields.Float(
        string='Estimated Weight (KG)'
    )
    
    estimated_volume = fields.Float(
        string='Estimated Volume (CBM)'
    )
    
    # Dates
    quotation_date = fields.Date(
        string='Quotation Date',
        default=fields.Date.today,
        required=True
    )
    
    validity_date = fields.Date(
        string='Valid Until',
        required=True,
        default=lambda self: fields.Date.today() + timedelta(days=30)
    )
    
    # Financial
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    cost_line_ids = fields.One2many(
        'freight.cost.line',
        'quotation_id',
        string='Cost Lines'
    )
    
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True
    )
    
    shipment_id = fields.Many2one(
        'freight.shipment',
        string='Related Shipment',
        readonly=True
    )
    
    terms_conditions = fields.Text(
        string='Terms and Conditions'
    )
    
    internal_notes = fields.Text(
        string='Internal Notes'
    )

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('freight.quotation') or _('New')
        return super(FreightQuotation, self).create(vals)

    @api.depends('cost_line_ids.amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.cost_line_ids.mapped('amount'))

    def action_send_quotation(self):
        """Send quotation to customer"""
        self.write({'state': 'sent'})
        return True

    def action_confirm(self):
        """Confirm quotation"""
        self.write({'state': 'confirmed'})
        return True
    
    def action_create_shipment(self):
        """Create shipment from confirmed quotation"""
        if self.state != 'confirmed':
            return False
            
        # Create shipment from quotation
        shipment_vals = {
            'customer_id': self.customer_id.id,
            'origin_port_id': self.origin_port_id.id,
            'destination_port_id': self.destination_port_id.id,
            'transport_mode': self.transport_mode,
            'service_type': self.service_type,
            'cargo_description': self.cargo_description,
            'total_weight': self.estimated_weight,
            'total_volume': self.estimated_volume,
            'state': 'booking'
        }
        
        shipment = self.env['freight.shipment'].create(shipment_vals)
        
        # Create cost lines from quotation cost lines
        for line in self.cost_line_ids:
            self.env['freight.cost.line'].create({
                'shipment_id': shipment.id,
                'cost_type': 'sell',
                'cost_category': line.cost_category,
                'description': line.description,
                'amount': line.amount,
                'partner_id': self.customer_id.id
            })
        
        self.shipment_id = shipment.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Shipment',
            'res_model': 'freight.shipment',
            'res_id': shipment.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_expire(self):
        """Mark quotation as expired"""
        self.write({'state': 'expired'})
        return True
    
    def action_reset_to_draft(self):
        """Reset quotation to draft"""
        self.write({'state': 'draft'})
        return True

    def action_cancel(self):
        """Cancel quotation"""
        self.write({'state': 'cancelled'})
        return True
