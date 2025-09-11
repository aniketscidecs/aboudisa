from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightIncoterm(models.Model):
    _name = 'freight.incoterm'
    _description = 'Freight Incoterms Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'
    _rec_name = 'name'

    code = fields.Char(
        string='Incoterm Code',
        required=True,
        size=10,
        tracking=True,
        help='Standard incoterm code (e.g., EXW, FOB, CIF)'
    )
    name = fields.Char(
        string='Description',
        required=True,
        tracking=True,
        help='Full description of the incoterm'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide the incoterm without removing it'
    )
    
    # Incoterm details
    incoterm_group = fields.Selection([
        ('e', 'E - Departure'),
        ('f', 'F - Main Carriage Unpaid'),
        ('c', 'C - Main Carriage Paid'),
        ('d', 'D - Arrival')
    ], string='Incoterm Group', tracking=True, help='Incoterm classification group')
    
    transport_mode = fields.Selection([
        ('any', 'Any Mode of Transport'),
        ('sea_inland', 'Sea and Inland Waterway Transport Only'),
        ('multimodal', 'Multimodal Transport')
    ], string='Transport Mode', default='any', tracking=True, help='Applicable transport modes')
    
    # Risk and cost transfer
    risk_transfer_point = fields.Text(
        string='Risk Transfer Point',
        help='Point where risk transfers from seller to buyer'
    )
    cost_responsibility = fields.Text(
        string='Cost Responsibility',
        help='Description of cost responsibilities'
    )
    
    # Insurance and documentation
    insurance_required = fields.Boolean(
        string='Insurance Required',
        help='Whether insurance is required by seller'
    )
    export_clearance = fields.Selection([
        ('seller', 'Seller Responsibility'),
        ('buyer', 'Buyer Responsibility'),
        ('na', 'Not Applicable')
    ], string='Export Clearance', default='seller', help='Who handles export clearance')
    
    import_clearance = fields.Selection([
        ('seller', 'Seller Responsibility'),
        ('buyer', 'Buyer Responsibility'),
        ('na', 'Not Applicable')
    ], string='Import Clearance', default='buyer', help='Who handles import clearance')
    
    # Additional information
    year_version = fields.Char(
        string='Incoterms Version',
        default='2020',
        help='Incoterms version year (e.g., 2020, 2010)'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional information about the incoterm'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure incoterm code is unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Incoterm code must be unique. Code "%s" already exists.') % record.code)

    @api.constrains('code')
    def _check_code_format(self):
        """Validate incoterm code format"""
        for record in self:
            if record.code:
                # Check if it's a valid format (2-10 letters typically)
                if not record.code.isalpha() or len(record.code) < 2 or len(record.code) > 10:
                    raise ValidationError(_('Incoterm code should be 2-10 alphabetic characters.'))

    @api.model
    def create(self, vals):
        """Override create to ensure code is uppercase"""
        if 'code' in vals and vals['code']:
            vals['code'] = vals['code'].upper()
        return super().create(vals)

    def write(self, vals):
        """Override write to ensure code is uppercase"""
        if 'code' in vals and vals['code']:
            vals['code'] = vals['code'].upper()
        return super().write(vals)

    def name_get(self):
        """Custom name display: CODE - Description"""
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced search by code or description"""
        args = args or []
        if name:
            incoterms = self.search([
                '|', ('code', operator, name.upper()), ('name', operator, name)
            ] + args, limit=limit)
            return incoterms.name_get()
        return super().name_search(name, args, operator, limit)

    @api.model
    def get_default_incoterms(self):
        """Return list of standard Incoterms 2020"""
        return [
            ('EXW', 'Ex Works'),
            ('FCA', 'Free Carrier'),
            ('CPT', 'Carriage Paid To'),
            ('CIP', 'Carriage and Insurance Paid To'),
            ('DAP', 'Delivered at Place'),
            ('DPU', 'Delivered at Place Unloaded'),
            ('DDP', 'Delivered Duty Paid'),
            ('FAS', 'Free Alongside Ship'),
            ('FOB', 'Free on Board'),
            ('CFR', 'Cost and Freight'),
            ('CIF', 'Cost, Insurance and Freight'),
        ]
