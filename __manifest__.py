# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{ 'name': 'HR Prestamos',
'summary': "Prestamos",
'author': "Mauricio Gah",
'license': "AGPL-3",
'application': "True",
'version': "2.0",
'data': ['security/ir.model.access.csv',    
         'securiry/grous.xml' 
         'views/menu.xml',
         'views/prestamo.xml',
        
],

'depends': ['base' , 'contacts' , 'hr' , 'parches_insumar'],
'installable': True,
'application': True,
}
