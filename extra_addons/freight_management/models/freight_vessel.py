from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightVessel(models.Model):
    _name = 'freight.vessel'
    _description = 'Freight Vessel Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    code = fields.Char(
        string='Vessel Code',
        required=True,
        size=20,
        tracking=True,
        help='Unique vessel identification code'
    )
    name = fields.Char(
        string='Vessel Name',
        required=True,
        tracking=True,
        help='Full name of the vessel'
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        tracking=True,
        help='Country of vessel registration'
    )
    global_zone = fields.Char(
        string='Global Zone',
        tracking=True,
        help='Global operational zone of the vessel'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide the vessel without removing it'
    )
    
    # Additional vessel information
    vessel_type = fields.Selection([
        ('container', 'Container Ship'),
        ('bulk', 'Bulk Carrier'),
        ('tanker', 'Tanker'),
        ('roro', 'RoRo Ship'),
        ('general', 'General Cargo'),
        ('other', 'Other')
    ], string='Vessel Type', tracking=True, help='Type of vessel')
    
    imo_number = fields.Char(
        string='IMO Number',
        size=10,
        help='International Maritime Organization number'
    )
    mmsi_number = fields.Char(
        string='MMSI Number',
        size=15,
        help='Maritime Mobile Service Identity number'
    )
    call_sign = fields.Char(
        string='Call Sign',
        size=10,
        help='Vessel call sign'
    )
    
    # Capacity information
    gross_tonnage = fields.Float(
        string='Gross Tonnage',
        help='Gross tonnage of the vessel'
    )
    net_tonnage = fields.Float(
        string='Net Tonnage',
        help='Net tonnage of the vessel'
    )
    deadweight = fields.Float(
        string='Deadweight (MT)',
        help='Deadweight tonnage in metric tons'
    )
    teu_capacity = fields.Integer(
        string='TEU Capacity',
        help='Twenty-foot Equivalent Unit capacity'
    )
    
    # Dimensions
    length = fields.Float(
        string='Length (m)',
        help='Overall length in meters'
    )
    beam = fields.Float(
        string='Beam (m)',
        help='Beam width in meters'
    )
    draft = fields.Float(
        string='Draft (m)',
        help='Maximum draft in meters'
    )
    
    # Operational details
    owner_id = fields.Many2one(
        'res.partner',
        string='Owner',
        help='Vessel owner company'
    )
    operator_id = fields.Many2one(
        'res.partner',
        string='Operator',
        help='Vessel operating company'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional information about the vessel'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure vessel code is unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Vessel code must be unique. Code "%s" already exists.') % record.code)

    @api.constrains('imo_number')
    def _check_imo_number(self):
        """Validate IMO number format"""
        for record in self:
            if record.imo_number:
                # Basic IMO number validation (should be 7 digits)
                if not record.imo_number.isdigit() or len(record.imo_number) != 7:
                    raise ValidationError(_('IMO number must be exactly 7 digits.'))

    def name_get(self):
        """Custom name display: [CODE] Name"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.country_id:
                name += f" ({record.country_id.code})"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced search by code or name"""
        args = args or []
        if name:
            vessels = self.search([
                '|', ('code', operator, name), ('name', operator, name)
            ] + args, limit=limit)
            return vessels.name_get()
        return super().name_search(name, args, operator, limit)
