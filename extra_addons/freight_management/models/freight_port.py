from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightPort(models.Model):
    _name = 'freight.port'
    _description = 'Freight Port Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    code = fields.Char(
        string='Port Code',
        required=True,
        size=10,
        tracking=True,
        help='Unique port identification code'
    )
    name = fields.Char(
        string='Port Name',
        required=True,
        tracking=True,
        help='Full name of the port'
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        tracking=True,
        help='Country where the port is located'
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='State/Province',
        tracking=True,
        help='State or province where the port is located'
    )
    
    # Transport mode support
    air_supported = fields.Boolean(
        string='Air',
        default=False,
        tracking=True,
        help='Port supports air freight operations'
    )
    ocean_supported = fields.Boolean(
        string='Ocean',
        default=False,
        tracking=True,
        help='Port supports ocean freight operations'
    )
    land_supported = fields.Boolean(
        string='Land',
        default=False,
        tracking=True,
        help='Port supports land freight operations'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide the port without removing it'
    )
    
    # Additional fields for better functionality
    timezone = fields.Selection(
        selection='_get_timezone_selection',
        string='Timezone',
        help='Port timezone for scheduling purposes'
    )
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help='Port latitude coordinates'
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help='Port longitude coordinates'
    )
    notes = fields.Text(
        string='Notes',
        help='Additional information about the port'
    )

    @api.model
    def _get_timezone_selection(self):
        """Get timezone selection list"""
        import pytz
        return [(tz, tz) for tz in pytz.all_timezones]

    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure port code is unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Port code must be unique. Code "%s" already exists.') % record.code)

    @api.constrains('air_supported', 'ocean_supported', 'land_supported')
    def _check_transport_mode(self):
        """Ensure at least one transport mode is supported"""
        for record in self:
            if not any([record.air_supported, record.ocean_supported, record.land_supported]):
                raise ValidationError(_('Port must support at least one transport mode (Air, Ocean, or Land).'))

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clear state when country changes"""
        if self.country_id:
            self.state_id = False

    def name_get(self):
        """Custom name display: [CODE] Name, Country"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.country_id:
                name += f", {record.country_id.name}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced search by code or name"""
        args = args or []
        if name:
            # Search by code or name
            ports = self.search([
                '|', ('code', operator, name), ('name', operator, name)
            ] + args, limit=limit)
            return ports.name_get()
        return super().name_search(name, args, operator, limit)
