from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import math

class Prestamo(models.Model):
    _name = 'hr.prestamo'
    _description = 'Prestamos a empleados'

    name = fields.Integer(string='ID', index=True)
    nombre = fields.Many2one('hr.employee', string='Empleado', required=True) 
    monto = fields.Integer(string='Monto del Préstamo', required=True)
    nro_cuotas = fields.Integer(string='Nro Cuotas', required=True)
    cuota = fields.Integer(string='Cuota', compute='_compute_cuota', store=True)
    restante = fields.Integer(string='Cuotas Restantes')
    saldo = fields.Integer(string='Saldo Restante')
    fecha = fields.Date(string='Fecha de Solicitud')
    activo = fields.Boolean(string='Activo', default=False, readonly=True)
    mes_inicio = fields.Selection(
        selection=[
            ('actual', 'Mes actual'),
            ('siguiente', 'Mes siguiente'),
        ],
        string='Inicio de cobro',
        default='actual',
        required=True
    )

    @api.depends('monto', 'nro_cuotas')
    def _compute_cuota(self):
        for record in self:
            if record.monto and record.nro_cuotas:
                record.cuota = math.ceil(record.monto / record.nro_cuotas)
            else:
                record.cuota = 0

    @api.constrains('nro_cuotas')
    def _check_cuota(self):
        for record in self:
            if record.nro_cuotas and record.nro_cuotas <= 0:
                raise ValidationError("El número de cuotas no puede ser 0 o menor.")

    @api.model
    def create(self, vals):
        # Al crear, activar el préstamo e inicializar campos
        vals.update({
            'activo': True,
            'restante': vals.get('nro_cuotas', 0),
            'saldo': vals.get('monto', 0),
        })
        return super().create(vals)

    def write(self, vals):
        # Permitir escritura programática (ej: desde otro módulo)
        if not self.env.context.get('bypass_protection'):
            # Si no es programático, bloquear edición si está activo
            for record in self:
                if record.activo:
                    raise UserError(_("No puedes editar un préstamo activo desde la vista."))
        return super().write(vals)

    def unlink(self):
        # Permitir eliminación programática
        if not self.env.context.get('bypass_protection'):
            for record in self:
                if record.activo:
                    raise UserError(_("No puedes eliminar un préstamo activo desde la vista."))
        return super().unlink()
