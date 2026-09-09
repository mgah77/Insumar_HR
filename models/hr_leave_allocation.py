# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime

from odoo import models

_logger = logging.getLogger(__name__)

# --- Configuración ---
TIPO_ID = 7                      # hr.leave.type "Administrativo"
TIPO_NOMBRE = 'Administrativo'   # respaldo por si el id cambia
DIAS = 4.0


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    def _cron_asignar_dias_administrativos(self):
        """Cada 1 de marzo: 4 días del tipo 'Administrativo' para todos
        los empleados activos, vigentes hasta el 30 de noviembre."""
        self = self.sudo()  # el cron puede ejecutarse con usuario sin permisos de RRHH
        env = self.env

        # 1) Localizar el tipo de ausencia
        leave_type = env['hr.leave.type'].browse(TIPO_ID)
        if not leave_type.exists():
            leave_type = env['hr.leave.type'].search(
                [('name', '=ilike', TIPO_NOMBRE)], limit=1)
        if not leave_type:
            _logger.warning(
                'Cron días administrativos: no se encontró el tipo de ausencia '
                '(id=%s, nombre=%s)', TIPO_ID, TIPO_NOMBRE)
            return

        anio = date.today().year
        fecha_desde = datetime(anio, 3, 1)
        fecha_hasta = datetime(anio, 11, 30, 23, 59, 59)  # nov. tiene 30 días

        # 2) Empleados activos
        dominio = [('active', '=', True)]
        if leave_type.company_id:
            dominio.append(('company_id', '=', leave_type.company_id.id))
        empleados = env['hr.employee'].search(dominio)
        if not empleados:
            return

        # 3) Idempotencia: saltar a quienes ya se les asignó este año
        ya_tienen = env['hr.leave.allocation'].search([
            ('holiday_status_id', '=', leave_type.id),
            ('employee_id', 'in', empleados.ids),
            ('date_from', '>=', datetime(anio, 1, 1)),
            ('date_from', '<=', datetime(anio, 12, 31, 23, 59, 59)),
            ('state', 'not in', ['refuse', 'cancel']),
        ]).mapped('employee_id')

        vals_base = {
            'name': 'Días administrativos %s (carga anual automática)' % anio,
            'holiday_status_id': leave_type.id,
            'holiday_type': 'employee',
            'allocation_type': 'regular',
            'number_of_days': DIAS,
            'date_from': fecha_desde,
            'date_to': fecha_hasta,
        }

        for emp in empleados - ya_tienen:
            alloc = env['hr.leave.allocation'].create({
                **vals_base,
                'employee_id': emp.id,
                'company_id': emp.company_id.id,
            })
            # Flujo normal: confirmar -> aprobar
            if alloc.state == 'draft':
                alloc.action_confirm()
            if alloc.state == 'confirm':
                alloc.action_approve()
            # Red de seguridad (p. ej. si el tipo pide doble validación)
            if alloc.state != 'validate':
                alloc.write({'state': 'validate'})
            _logger.info(
                'Días administrativos: +%s días a %s (id=%s)',
                DIAS, emp.name, emp.id)