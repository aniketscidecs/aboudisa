from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightAirline(models.Model):
    _name = 'freight.airline'
    _description = 'Freight Airline Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    code = fields.Char(
        string='Airline Code',
        required=True,
        size=10,
        tracking=True,
        help='Unique airline identification code (IATA/ICAO)'
    )
    name = fields.Char(
        string='Airline Name',
        required=True,
        tracking=True,
        help='Full name of the airline'
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        tracking=True,
        help='Country of airline registration'
    )
    icao_code = fields.Char(
        string='ICAO Code',
        size=4,
        tracking=True,
        help='International Civil Aviation Organization code'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide the airline without removing it'
    )
    
    # Additional airline information
    iata_code = fields.Char(
        string='IATA Code',
        size=3,
        tracking=True,
        help='International Air Transport Association code'
    )
    airline_type = fields.Selection([
        ('passenger', 'Passenger'),
        ('cargo', 'Cargo Only'),
        ('mixed', 'Mixed (Passenger & Cargo)'),
        ('charter', 'Charter')
    ], string='Airline Type', default='mixed', tracking=True, help='Type of airline service')
    
    # Contact information
    website = fields.Char(
        string='Website',
        help='Airline official website'
    )
    phone = fields.Char(
        string='Phone',
        help='Airline contact phone number'
    )
    email = fields.Char(
        string='Email',
        help='Airline contact email'
    )
    
    # Operational details
    hub_airport_ids = fields.Many2many(
        'freight.port',
        'airline_hub_rel',
        'airline_id',
        'port_id',
        string='Hub Airports',
        domain=[('air_supported', '=', True)],
        help='Main hub airports for this airline'
    )
    
    # Fleet information
    fleet_size = fields.Integer(
        string='Fleet Size',
        help='Total number of aircraft in fleet'
    )
    cargo_fleet_size = fields.Integer(
        string='Cargo Fleet Size',
        help='Number of dedicated cargo aircraft'
    )
    
    # Service areas
    domestic_service = fields.Boolean(
        string='Domestic Service',
        default=True,
        help='Provides domestic flights'
    )
    international_service = fields.Boolean(
        string='International Service',
        default=True,
        help='Provides international flights'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional information about the airline'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure airline code is unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Airline code must be unique. Code "%s" already exists.') % record.code)

    @api.constrains('iata_code')
    def _check_iata_code(self):
        """Validate IATA code format"""
        for record in self:
            if record.iata_code:
                if len(record.iata_code) != 2 and len(record.iata_code) != 3:
                    raise ValidationError(_('IATA code must be 2 or 3 characters long.'))
                if not record.iata_code.isalpha():
                    raise ValidationError(_('IATA code must contain only letters.'))

    @api.constrains('icao_code')
    def _check_icao_code(self):
        """Validate ICAO code format"""
        for record in self:
            if record.icao_code:
                if len(record.icao_code) != 3 and len(record.icao_code) != 4:
                    raise ValidationError(_('ICAO code must be 3 or 4 characters long.'))
                if not record.icao_code.isalnum():
                    raise ValidationError(_('ICAO code must contain only letters and numbers.'))

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
            airlines = self.search([
                '|', '|', ('code', operator, name), 
                ('name', operator, name), 
                ('iata_code', operator, name)
            ] + args, limit=limit)
            return airlines.name_get()
        return super().name_search(name, args, operator, limit)
