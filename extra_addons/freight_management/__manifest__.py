{
    'name': 'Freight Management',
    'version': '18.0.1.0.0',
    'category': 'Operations/Inventory',
    'summary': 'Comprehensive freight forwarding and logistics management',
    'description': """
        Freight Management Module for ABOUDi Logistics
        ==============================================
        
        This module provides comprehensive freight forwarding and logistics management capabilities:
        
        * Multi-modal transport support (Air, Ocean, Land)
        * FCL/LCL and FTL/LTL service types
        * Complete shipment lifecycle management
        * Cost management and quotation system
        * Configuration management for ports, vessels, airlines, incoterms, containers
        * Integration with Odoo's accounting and invoicing system
        
        Designed specifically for ABOUDi Logistics Services Co. operations in steel, 
        oil & gas, and geophysical industries across the Middle East region.
    """,
    'author': 'Scidecs',
    'website': 'https://www.scidecs.com',
    'depends': [
        'base',
        'mail',
        'sale',
        'stock',
        'account',
        'contacts',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/freight_data.xml',
        'data/freight_sequences.xml',
        'views/freight_port_views.xml',
        'views/freight_vessel_views.xml',
        'views/freight_airline_views.xml',
        'views/freight_incoterm_views.xml',
        'views/freight_container_views.xml',
        'views/freight_shipment_views.xml',
        'views/freight_cost_views.xml',
        'views/freight_menu.xml',
    ],
    'demo': [
        'demo/freight_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
