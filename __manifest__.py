# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{ 'name': 'RRHH Insumar',
'summary': "RRHH",
'author': "Mauricio Gah",
'license': "AGPL-3",
'application': "True",
'version': "2.0",
'data': ['security/ir.model.access.csv',    
         'security/groups.xml',
         'views/menu.xml',
         'views/employee.xml',
         'views/prestamo.xml',
         'views/hr_leave_views.xml'
        
],

'depends': ['base' , 'contacts' , 'hr' , 'parches_insumar','hr_holidays'],
'installable': True,
'application': True,
}
