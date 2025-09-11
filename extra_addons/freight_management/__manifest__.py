{
    'name': 'Freight Management',
    'version': '18.0.1.0.0',
    'category': 'Logistics',
    'summary': 'Comprehensive Freight Forwarding Management System',
    'description': """
        Freight Management System for ABOUDi Logistics Services Co.
        
        Features:
        - Multi-modal transport management (Air, Ocean, Land)
        - FCL/LCL and FTL/LTL shipment handling
        - Comprehensive configuration management
        - Ports, Vessels, Airlines, Incoterms, and Container configurations
        - Designed for steel, oil & gas, and geophysical industries
    """,
    'author': 'Scidecs',
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
        'views/freight_port_views.xml',
        'views/freight_vessel_views.xml',
        'views/freight_airline_views.xml',
        'views/freight_incoterm_views.xml',
        'views/freight_container_views.xml',
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
