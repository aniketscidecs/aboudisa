from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightContainer(models.Model):
    _name = 'freight.container'
    _description = 'Freight Container/Package Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    code = fields.Char(
        string='Container/Package Code',
        required=True,
        size=20,
        tracking=True,
        help='Unique container or package identification code'
    )
    name = fields.Char(
        string='Container/Package Name',
        required=True,
        tracking=True,
        help='Full name or description of the container/package'
    )
    
    # Container classification
    is_container = fields.Boolean(
        string='Is Container',
        default=True,
        tracking=True,
        help='Check if this is a shipping container, uncheck for packages'
    )
    refrigerated = fields.Boolean(
        string='Refrigerated',
        default=False,
        tracking=True,
        help='Container/package supports refrigeration'
    )
    
    # Dimensions and capacity
    size = fields.Float(
        string='Size (ft)',
        help='Container size in feet (e.g., 20, 40)'
    )
    volume = fields.Float(
        string='Volume (m³)',
        help='Internal volume in cubic meters'
    )
    max_weight = fields.Float(
        string='Max Weight (kg)',
        help='Maximum weight capacity in kilograms'
    )
    
    # Physical dimensions
    length = fields.Float(
        string='Length (m)',
        help='Internal length in meters'
    )
    width = fields.Float(
        string='Width (m)',
        help='Internal width in meters'
    )
    height = fields.Float(
        string='Height (m)',
        help='Internal height in meters'
    )
    
    # External dimensions
    external_length = fields.Float(
        string='External Length (m)',
        help='External length in meters'
    )
    external_width = fields.Float(
        string='External Width (m)',
        help='External width in meters'
    )
    external_height = fields.Float(
        string='External Height (m)',
        help='External height in meters'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide the container/package without removing it'
    )
    
    # Container type details
    container_type = fields.Selection([
        ('dry', 'Dry Container'),
        ('reefer', 'Refrigerated Container'),
        ('open_top', 'Open Top Container'),
        ('flat_rack', 'Flat Rack Container'),
        ('tank', 'Tank Container'),
        ('bulk', 'Bulk Container'),
        ('package', 'Package/Box'),
        ('pallet', 'Pallet'),
        ('other', 'Other')
    ], string='Type', tracking=True, help='Container or package type')
    
    # ISO standards
    iso_code = fields.Char(
        string='ISO Code',
        size=10,
        help='ISO 6346 container type code'
    )
    
    # Transport mode compatibility
    ocean_compatible = fields.Boolean(
        string='Ocean Compatible',
        default=True,
        help='Can be used for ocean freight'
    )
    air_compatible = fields.Boolean(
        string='Air Compatible',
        default=False,
        help='Can be used for air freight'
    )
    land_compatible = fields.Boolean(
        string='Land Compatible',
        default=True,
        help='Can be used for land freight'
    )
    
    # Special features
    hazmat_approved = fields.Boolean(
        string='Hazmat Approved',
        default=False,
        help='Approved for hazardous materials'
    )
    food_grade = fields.Boolean(
        string='Food Grade',
        default=False,
        help='Food grade certified'
    )
    
    # Pricing and costs
    daily_rate = fields.Float(
        string='Daily Rate',
        help='Daily rental/usage rate'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for rates'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional information about the container/package'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure container code is unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Container/Package code must be unique. Code "%s" already exists.') % record.code)

    @api.constrains('length', 'width', 'height')
    def _check_dimensions(self):
        """Validate dimensions are positive"""
        for record in self:
            if record.length and record.length <= 0:
                raise ValidationError(_('Length must be greater than zero.'))
            if record.width and record.width <= 0:
                raise ValidationError(_('Width must be greater than zero.'))
            if record.height and record.height <= 0:
                raise ValidationError(_('Height must be greater than zero.'))

    @api.depends('length', 'width', 'height')
    def _compute_volume(self):
        """Auto-calculate volume from dimensions"""
        for record in self:
            if record.length and record.width and record.height:
                record.volume = record.length * record.width * record.height
            else:
                record.volume = 0

    @api.onchange('is_container')
    def _onchange_is_container(self):
        """Set default values based on container type"""
        if self.is_container:
            self.ocean_compatible = True
            self.land_compatible = True
            self.air_compatible = False
        else:
            # For packages
            self.air_compatible = True
            self.ocean_compatible = True
            self.land_compatible = True

    @api.onchange('refrigerated')
    def _onchange_refrigerated(self):
        """Set container type when refrigerated is checked"""
        if self.refrigerated and self.is_container:
            self.container_type = 'reefer'

    def name_get(self):
        """Custom name display: [CODE] Name (Size)"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.size:
                name += f" ({record.size}ft)"
            elif record.volume:
                name += f" ({record.volume}m³)"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced search by code or name"""
        args = args or []
        if name:
            containers = self.search([
                '|', ('code', operator, name), ('name', operator, name)
            ] + args, limit=limit)
            return containers.name_get()
        return super().name_search(name, args, operator, limit)

    @api.model
    def get_standard_containers(self):
        """Return list of standard container types"""
        return [
            ('20DC', '20ft Dry Container', 20, 33.2),
            ('40DC', '40ft Dry Container', 40, 67.7),
            ('40HC', '40ft High Cube Container', 40, 76.4),
            ('20RF', '20ft Refrigerated Container', 20, 28.3),
            ('40RF', '40ft Refrigerated Container', 40, 59.3),
            ('20OT', '20ft Open Top Container', 20, 32.6),
            ('40OT', '40ft Open Top Container', 40, 65.9),
            ('20FR', '20ft Flat Rack Container', 20, 0),
            ('40FR', '40ft Flat Rack Container', 40, 0),
        ]
