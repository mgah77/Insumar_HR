# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccrualPlanLevel(models.Model):
    _inherit = 'hr.leave.accrual.level'

    start_reference = fields.Selection([
        ('allocation', 'Fecha de la asignación'),
        ('hire', 'Fecha de ingreso del empleado'),
    ], string='Fecha de inicio', default='allocation', required=True,
        groups='hr.group_hr_user',
        help='Fecha desde la que se cuenta el devengo de esta regla.\n'
             '- Fecha de la asignación: comportamiento estándar de Odoo.\n'
             '- Fecha de ingreso del empleado: usa el campo "ingreso" de la '
             'ficha del empleado.')

    frequency = fields.Selection([
        ('daily', 'Diaria'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual (día fijo)'),
        ('monthly_hire', 'Mensual (aniversario de ingreso)'),
    ], default='daily', required=True, string='Frecuencia')

    _sql_constraints = [
        ('check_dates',
         "CHECK( (frequency = 'daily') or"
         "(week_day IS NOT NULL AND frequency = 'weekly') or "
         "(first_day > 0 AND second_day > first_day AND first_day <= 31 AND second_day <= 31 AND frequency = 'bimonthly') or "
         "(first_day > 0 AND first_day <= 31 AND frequency = 'monthly') or "
         "(frequency = 'monthly_hire') or "
         "(first_month_day > 0 AND first_month_day <= 31 AND second_month_day > 0 AND second_month_day <= 31 AND frequency = 'biyearly') or "
         "(yearly_day > 0 AND yearly_day <= 31 AND frequency = 'yearly'))",
         "The dates you've set up aren't correct. Please check them."),
    ]

    def _get_next_date(self, last_call):
        self.ensure_one()
        if self.frequency == 'monthly_hire':
            hire_day = self.env.context.get('accrual_hire_day')
            if hire_day:
                # Día absoluto: si el mes no tiene ese día, se ajusta al
                # último día del mes (30 -> 28/29 en febrero, 31 -> 30 en abril)
                return last_call + relativedelta(months=1, day=hire_day)
            return last_call + relativedelta(months=1)
        return super()._get_next_date(last_call)

    def _get_previous_date(self, last_call):
        # last_call siempre cae en un corte válido: el periodo completo es
        # [last_call, last_call + 1 mes] -> sin prorrateo
        self.ensure_one()
        if self.frequency == 'monthly_hire':
            return last_call
        return super()._get_previous_date(last_call)