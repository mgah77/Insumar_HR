from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ParcheHR(models.Model):
    _inherit = 'hr.employee'

    address_home_id = fields.Many2one(
        'res.partner', 'Private Address',
        help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        context="{'default_type': 'private', 'default_company_id': company_id, 'form_view_ref': 'base.view_partner_address_form'}",
    )

    certificate = fields.Selection([
        ('basica','Basica'),
        ('media','Media'),
        ('superior','Superior')], 'Nivel de Estudios', default='media')

    afp = fields.Selection([
        ('capital','AFP Capital'),
        ('cuprum','AFP Cuprum'),
        ('habitat','AFP Habitat'),
        ('modelo','AFP Modelo'),
        ('planvital','AFP Planvital'),
        ('provida','AFP Provida'),
        ('uno','AFP Uno')], 'AFP')
    
    salud = fields.Selection([
        ('fonasa','Fonasa'),
        ('banmedica','Banmedica'),
        ('colmena','Colmena'),
        ('consalud','Consalud'),
        ('cruzblanca','Cruz Blanca'),
        ('masvida','Masvida'),
        ('vidatres','Vida Tres')], 'Sistema de Salud')

    caja = fields.Selection([
        ('andes','CCAF Los Andes'),
        ('araucana','CCAF La Araucana'),
        ('heroes','CCAF Los Heroes'),
        ('18','CCAF 18 de Septiembre')], 'Caja de Compensacion')

    sueldo = fields.Integer(string='Base', default=0)
    bono_prod = fields.Integer(string='Producción', default=0)
    bono_resp = fields.Integer(string='Responsabilidad', default=0)
    bono_resp_taller = fields.Integer(string='Responsabilidad Taller', default=0)
    bono_comi = fields.Integer(string='Comision Taller', default=0)
    bono_punt = fields.Integer(string='Puntualidad', default=0)
    bono_asist = fields.Integer(string='Asistencia', default=0)
    bono_movil = fields.Integer(string='Movilizacion', default=0)
    bono_colac = fields.Integer(string='Colacion', default=0)
    bono_estud = fields.Integer(string='Estudio', default=0)
    bono_estud_esp = fields.Integer(string='Estudio Especial', default=0)
    capac = fields.Html(string='Capacitaciones y/o Cursos')

    jornada = fields.Selection([
        ('completa','Completa'),
        ('parcial','Parcial')], 'Jornada Laboral')
    horas = fields.Integer('Horas Semanales')

    banco = fields.Char(string = 'Banco')
    cuenta_banco = fields.Char(string='Cuenta')
    cuenta_tipo = fields.Selection([
        ('cc','Cuenta Corriente'),
        ('vi','Cuenta Vista'),
        ('ah','Cuenta Ahorro')], 'Tipo de cuenta')
    