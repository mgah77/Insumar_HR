# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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


    previous_days = fields.Float(
        string='Días anteriores',
        groups='hr.group_hr_user',
        help='Días acumulados antes del inicio del devengo de este plan '
             '(años anteriores, otro sistema). Se suman al total junto con '
             'el devengo retroactivo.')
    uses_hire_date = fields.Boolean(
        compute='_compute_uses_hire_date', groups='hr.group_hr_user')

    @api.depends('accrual_plan_id.level_ids.start_reference')
    def _compute_uses_hire_date(self):
        for allocation in self:
            allocation.uses_hire_date = any(
                level.start_reference == 'hire'
                for level in allocation.accrual_plan_id.sudo().level_ids)

    def _plan_uses_hire_date(self):
        """Lectura segura de start_reference (sudo): la lógica puede correr
        con usuarios fuera de hr.group_hr_user, que no ven el campo."""
        self.ensure_one()
        if not self.accrual_plan_id:
            return False
        return any(level.start_reference == 'hire'
                   for level in self.accrual_plan_id.sudo().level_ids)

    @api.model
    def _get_retro_start(self, employee):
        """Inicio del devengo retroactivo:
        - fecha de ingreso si ingresó este año
        - último aniversario anual cumplido si ingresó en años anteriores"""
        hire_date = employee.sudo().ingreso
        if not hire_date:
            return False
        today = fields.Date.context_today(self)
        if hire_date.year >= today.year:
            return hire_date
        last_anniversary = hire_date + relativedelta(year=today.year)
        if last_anniversary > today:
            last_anniversary = hire_date + relativedelta(year=today.year - 1)
        return last_anniversary

    @api.onchange('employee_id', 'accrual_plan_id')
    def _onchange_hire_date_accrual(self):
        if (self.allocation_type == 'accrual'
                and self._plan_uses_hire_date()
                and self.employee_id):
            hire_date = self.employee_id.sudo().ingreso
            if hire_date:
                self.date_from = hire_date

    @api.onchange('previous_days')
    def _onchange_previous_days(self):
        if (self.allocation_type == 'accrual'
                and self._plan_uses_hire_date()
                and not self.nextcall):
            self.number_of_days = self.previous_days

    @api.model_create_multi
    def create(self, vals_list):
        Plan = self.env['hr.leave.accrual.plan']
        Employee = self.env['hr.employee']
        for values in vals_list:
            plan = Plan.browse(values.get('accrual_plan_id'))
            if any(level.start_reference == 'hire'
                   for level in plan.sudo().level_ids):
                employee = Employee.browse(values.get('employee_id'))
                if employee.sudo().ingreso:
                    values['date_from'] = employee.sudo().ingreso
                    if 'lastcall' not in values:
                        values['lastcall'] = self._get_retro_start(employee)
                if values.get('previous_days') and not values.get('number_of_days'):
                    values['number_of_days'] = values['previous_days']
        return super().create(vals_list)

    @api.constrains('state', 'accrual_plan_id', 'employee_id')
    def _check_hire_date_set(self):
        for allocation in self:
            if (allocation.state in ('confirm', 'validate')
                    and allocation.allocation_type == 'accrual'
                    and allocation._plan_uses_hire_date()
                    and allocation.employee_id
                    and not allocation.employee_id.sudo().ingreso):
                raise ValidationError(_(
                    "El empleado %s no tiene fecha de ingreso ('ingreso') en su ficha.",
                    allocation.employee_id.name))

    def _get_monthly_hire_day(self):
        """Día del mes para 'Mensual (aniversario de ingreso)': día de ingreso
        si la regla referencia el ingreso, día de la asignación si no."""
        self.ensure_one()
        level = self.accrual_plan_id.sudo().level_ids.filtered(
            lambda l: l.frequency == 'monthly_hire')[:1]
        if not level:
            return False
        if level.start_reference == 'hire' and self.employee_id.sudo().ingreso:
            return self.employee_id.sudo().ingreso.day
        return self.date_from.day

    def _process_accrual_plans(self, date_to=False, force_period=False):
        hire_allocations = self.filtered(
            lambda a: a.accrual_plan_id.level_ids.filtered(
                lambda l: l.frequency == 'monthly_hire'))
        for allocation in hire_allocations:
            day = allocation._get_monthly_hire_day()
            super(HrLeaveAllocation,
                  allocation.with_context(accrual_hire_day=day)
                  )._process_accrual_plans(date_to, force_period)
        others = self - hire_allocations
        if others:
            super(HrLeaveAllocation, others)._process_accrual_plans(date_to, force_period)

    def _end_of_year_accrual(self):
        hire_allocations = self.filtered(
            lambda a: a.accrual_plan_id.level_ids.filtered(
                lambda l: l.frequency == 'monthly_hire'))
        for allocation in hire_allocations:
            day = allocation._get_monthly_hire_day()
            super(HrLeaveAllocation,
                  allocation.with_context(accrual_hire_day=day)
                  )._end_of_year_accrual()
        others = self - hire_allocations
        if others:
            super(HrLeaveAllocation, others)._end_of_year_accrual()