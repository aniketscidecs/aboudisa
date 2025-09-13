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
    
    product_id = fields.Many2one(
        'product.product',
        string='Service Product',
        required=False,  # Temporarily non-required for migration
        domain=[('type', '=', 'service')],
        help='Service product representing this cost category'
    )
    
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        store=True,
        readonly=True
    )
    
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
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update description and unit price when product is selected"""
        if self.product_id:
            self.description = self.product_id.name
            if self.cost_type == 'sell':
                self.unit_price = self.product_id.list_price
            else:
                self.unit_price = self.product_id.standard_price
    
    @api.onchange('quantity', 'unit_price')
    def _onchange_quantity_unit_price(self):
        """Calculate amount when quantity or unit price changes"""
        self.amount = self.quantity * self.unit_price
    
    def _migrate_cost_category_to_product(self):
        """Migration method to convert cost_category to product_id"""
        # Get all cost lines without product_id
        cost_lines = self.search([('product_id', '=', False)])
        
        # Default service product mapping
        default_product = self.env.ref('freight_management.product_other_charges', raise_if_not_found=False)
        if not default_product:
            # Create a default service product if it doesn't exist
            default_product = self.env['product.product'].create({
                'name': 'Freight Service',
                'type': 'service',
                'sale_ok': True,
                'purchase_ok': True,
                'list_price': 0.0,
                'standard_price': 0.0,
            })
        
        # Update cost lines with default product
        for line in cost_lines:
            line.write({
                'product_id': default_product.id,
                'quantity': 1.0,
                'unit_price': line.amount or 0.0,
            })
        
        return True


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
    
    # Sales Integration
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
        copy=False,
        help='Sale order created from this quotation'
    )
    
    order_count = fields.Integer(
        string='Sale Order Count',
        compute='_compute_order_count'
    )
    
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count'
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
    
    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = 1 if record.sale_order_id else 0
    
    def _compute_invoice_count(self):
        for record in self:
            if record.sale_order_id:
                record.invoice_count = len(record.sale_order_id.invoice_ids)
            else:
                record.invoice_count = 0

    def action_send_quotation(self):
        """Send quotation to customer"""
        self.write({'state': 'sent'})
        return True

    def action_confirm(self):
        """Confirm quotation and create sale order"""
        if not self.cost_line_ids:
            raise ValidationError(_("Cannot confirm quotation without cost lines."))
        
        # Create sale order
        sale_order_vals = {
            'partner_id': self.customer_id.id,
            'date_order': fields.Datetime.now(),
            'validity_date': self.validity_date,
            'origin': self.reference,
            'note': self.terms_conditions,
            'freight_quotation_id': self.id,
        }
        
        sale_order = self.env['sale.order'].create(sale_order_vals)
        
        # Create sale order lines from cost lines
        for cost_line in self.cost_line_ids.filtered(lambda l: l.cost_type == 'sell'):
            sale_line_vals = {
                'order_id': sale_order.id,
                'product_id': cost_line.product_id.id,
                'name': cost_line.description or cost_line.product_id.name,
                'product_uom_qty': cost_line.quantity,
                'product_uom': cost_line.product_uom_id.id,
                'price_unit': cost_line.unit_price,
            }
            self.env['sale.order.line'].create(sale_line_vals)
        
        # Update quotation
        self.write({
            'state': 'confirmed',
            'sale_order_id': sale_order.id
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
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
            'direction': self.direction,
            'service_type': self.service_type,
            'cargo_description': self.cargo_description or 'General Cargo',
            'total_weight': self.estimated_weight,
            'total_volume': self.estimated_volume,
            'quotation_id': self.id,  # Link shipment to quotation
            'state': 'booking'
        }
        
        shipment = self.env['freight.shipment'].create(shipment_vals)
        
        # Create cost lines from quotation cost lines
        for line in self.cost_line_ids:
            self.env['freight.cost.line'].create({
                'shipment_id': shipment.id,
                'cost_type': 'sell',
                'product_id': line.product_id.id,
                'description': line.description,
                'quantity': line.quantity,
                'unit_price': line.unit_price,
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

    def cancel_quotation(self):
        """Cancel quotation"""
        self.write({'state': 'cancelled'})
        return True
    
    def action_view_sale_order(self):
        """Smart button to view related sale order"""
        if not self.sale_order_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_invoice(self):
        """Smart button to view related invoices"""
        if not self.sale_order_id:
            return False
        
        invoices = self.sale_order_id.invoice_ids
        if not invoices:
            return False
        
        if len(invoices) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoices.id,
                'view_mode': 'form',
                'target': 'current'
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'res_model': 'account.move',
                'domain': [('id', 'in', invoices.ids)],
                'view_mode': 'list,form',
                'target': 'current'
            }
