from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class FreightShipment(models.Model):
    _name = 'freight.shipment'
    _description = 'Freight Shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'reference'

    # Basic Information
    reference = fields.Char(
        string='Shipment Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('booking', 'Booking'),
        ('documentation', 'Documentation'),
        ('departure', 'Departure'),
        ('in_transit', 'In Transit'),
        ('arrival', 'Arrival'),
        ('delivery', 'Delivery'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)

    # Customer Information
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('is_company', '=', True)],
        tracking=True
    )
    
    shipper_id = fields.Many2one(
        'res.partner',
        string='Shipper',
        tracking=True
    )
    
    consignee_id = fields.Many2one(
        'res.partner',
        string='Consignee',
        tracking=True
    )
    
    notify_party_id = fields.Many2one(
        'res.partner',
        string='Notify Party',
        tracking=True
    )

    # Route Information
    origin_port_id = fields.Many2one(
        'freight.port',
        string='Origin Port',
        required=True,
        tracking=True
    )
    
    destination_port_id = fields.Many2one(
        'freight.port',
        string='Destination Port',
        required=True,
        tracking=True
    )
    
    transport_mode = fields.Selection([
        ('air', 'Air Freight'),
        ('ocean', 'Ocean Freight'),
        ('land', 'Land Freight')
    ], string='Transport Mode', required=True, tracking=True)
    
    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], string='Direction', required=True, tracking=True, help='Indicates whether this is an import or export shipment')

    # Service Information
    service_type = fields.Selection([
        ('fcl', 'Full Container Load (FCL)'),
        ('lcl', 'Less than Container Load (LCL)'),
        ('ftl', 'Full Truck Load (FTL)'),
        ('ltl', 'Less than Truck Load (LTL)'),
        ('air_freight', 'Air Freight'),
        ('express', 'Express Service')
    ], string='Service Type', tracking=True)
    
    incoterm_id = fields.Many2one(
        'freight.incoterm',
        string='Incoterm',
        tracking=True
    )

    # Cargo Information
    cargo_description = fields.Text(
        string='Cargo Description',
        required=True,
        tracking=True
    )
    
    total_weight = fields.Float(
        string='Total Weight (KG)',
        tracking=True
    )
    
    total_volume = fields.Float(
        string='Total Volume (CBM)',
        tracking=True
    )
    
    number_of_packages = fields.Integer(
        string='Number of Packages',
        default=1,
        tracking=True
    )
    
    container_ids = fields.Many2many(
        'freight.container',
        string='Containers/Packages',
        tracking=True
    )

    # Carrier Information
    airline_id = fields.Many2one(
        'freight.airline',
        string='Airline',
        tracking=True
    )
    
    vessel_id = fields.Many2one(
        'freight.vessel',
        string='Vessel',
        tracking=True
    )
    
    voyage_flight_number = fields.Char(
        string='Voyage/Flight Number',
        tracking=True
    )

    # Dates
    booking_date = fields.Datetime(
        string='Booking Date',
        default=fields.Datetime.now,
        tracking=True
    )
    
    estimated_departure = fields.Datetime(
        string='Estimated Departure',
        tracking=True
    )
    
    actual_departure = fields.Datetime(
        string='Actual Departure',
        tracking=True
    )
    
    estimated_arrival = fields.Datetime(
        string='Estimated Arrival',
        tracking=True
    )
    
    actual_arrival = fields.Datetime(
        string='Actual Arrival',
        tracking=True
    )
    
    delivery_date = fields.Datetime(
        string='Delivery Date',
        tracking=True
    )

    # Cost Management
    cost_line_ids = fields.One2many(
        'freight.cost.line',
        'shipment_id',
        string='Cost Lines'
    )

    # Financial Fields
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    total_sell_cost = fields.Monetary(
        string='Total Sell Cost',
        currency_field='currency_id',
        compute='_compute_total_costs',
        store=True
    )
    
    total_buy_cost = fields.Monetary(
        string='Total Buy Cost',
        currency_field='currency_id',
        compute='_compute_total_costs',
        store=True
    )
    
    profit_margin = fields.Monetary(
        string='Profit Margin',
        currency_field='currency_id',
        compute='_compute_total_costs',
        store=True
    )

    # Documents and Notes
    special_instructions = fields.Text(
        string='Special Instructions'
    )
    
    internal_notes = fields.Text(
        string='Internal Notes'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Computed Fields
    days_in_transit = fields.Integer(
        string='Days in Transit',
        compute='_compute_transit_days'
    )

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('freight.shipment') or _('New')
        return super(FreightShipment, self).create(vals)

    @api.depends('actual_departure', 'actual_arrival')
    def _compute_transit_days(self):
        for record in self:
            if record.actual_departure and record.actual_arrival:
                delta = record.actual_arrival - record.actual_departure
                record.days_in_transit = delta.days
            else:
                record.days_in_transit = 0

    @api.depends('cost_line_ids')
    def _compute_total_costs(self):
        for record in self:
            sell_costs = sum(record.cost_line_ids.filtered(lambda x: x.cost_type == 'sell').mapped('amount'))
            buy_costs = sum(record.cost_line_ids.filtered(lambda x: x.cost_type == 'buy').mapped('amount'))
            record.total_sell_cost = sell_costs
            record.total_buy_cost = buy_costs
            record.profit_margin = sell_costs - buy_costs

    @api.constrains('origin_port_id', 'destination_port_id')
    def _check_ports(self):
        for record in self:
            if record.origin_port_id == record.destination_port_id:
                raise ValidationError(_('Origin and destination ports cannot be the same.'))

    @api.constrains('transport_mode', 'origin_port_id', 'destination_port_id')
    def _check_port_transport_compatibility(self):
        for record in self:
            if record.transport_mode == 'air':
                if not record.origin_port_id.air_supported or not record.destination_port_id.air_supported:
                    raise ValidationError(_('Selected ports must support air transport for air freight.'))
            elif record.transport_mode == 'ocean':
                if not record.origin_port_id.ocean_supported or not record.destination_port_id.ocean_supported:
                    raise ValidationError(_('Selected ports must support ocean transport for ocean freight.'))
            elif record.transport_mode == 'land':
                if not record.origin_port_id.land_supported or not record.destination_port_id.land_supported:
                    raise ValidationError(_('Selected ports must support land transport for land freight.'))

    def action_confirm_booking(self):
        """Confirm the shipment booking"""
        self.write({'state': 'booking'})
        return True

    def action_prepare_documentation(self):
        """Move to documentation stage"""
        self.write({'state': 'documentation'})
        return True

    def action_departure(self):
        """Mark shipment as departed"""
        self.write({
            'state': 'departure',
            'actual_departure': fields.Datetime.now()
        })
        return True

    def action_in_transit(self):
        """Mark shipment as in transit"""
        self.write({'state': 'in_transit'})
        return True

    def action_arrival(self):
        """Mark shipment as arrived"""
        self.write({
            'state': 'arrival',
            'actual_arrival': fields.Datetime.now()
        })
        return True

    def action_delivery(self):
        """Mark shipment as delivered"""
        self.write({
            'state': 'delivery',
            'delivery_date': fields.Datetime.now()
        })
        return True

    def action_cancel(self):
        """Cancel the shipment"""
        self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        """Reset shipment to draft"""
        self.write({'state': 'draft'})
        return True
