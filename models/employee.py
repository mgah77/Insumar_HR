from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ParcheHR(models.Model):
    _inherit = 'hr.employee'

    certificate = fields.Selection([
        ('basica', 'Basica'),
        ('media', 'Media'),
        ('superior', 'Superior')
    ], 'Nivel de Estudios', default='media',
       groups='hr.group_hr_user')

    afp = fields.Selection([
        ('capital', 'AFP Capital'),
        ('cuprum', 'AFP Cuprum'),
        ('habitat', 'AFP Habitat'),
        ('modelo', 'AFP Modelo'),
        ('planvital', 'AFP Planvital'),
        ('provida', 'AFP Provida'),
        ('uno', 'AFP Uno')
    ], 'AFP',
       groups='hr.group_hr_user')

    salud = fields.Selection([
        ('fonasa', 'Fonasa'),
        ('banmedica', 'Banmedica'),
        ('colmena', 'Colmena'),
        ('consalud', 'Consalud'),
        ('cruzblanca', 'Cruz Blanca'),
        ('masvida', 'Masvida'),
        ('vidatres', 'Vida Tres')
    ], 'Sistema de Salud',
       groups='hr.group_hr_user')

    caja = fields.Selection([
        ('andes', 'CCAF Los Andes'),
        ('araucana', 'CCAF La Araucana'),
        ('heroes', 'CCAF Los Heroes'),
        ('18', 'CCAF 18 de Septiembre')
    ], 'Caja de Compensacion',
       groups='hr.group_hr_user')

    sueldo = fields.Integer(
        string='Base',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_prod = fields.Integer(
        string='Producción',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_resp = fields.Integer(
        string='Responsabilidad',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_resp_taller = fields.Integer(
        string='Responsabilidad Taller',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_comi = fields.Integer(
        string='Comision Taller',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_punt = fields.Integer(
        string='Puntualidad',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_asist = fields.Integer(
        string='Asistencia',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_movil = fields.Integer(
        string='Movilizacion',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_colac = fields.Integer(
        string='Colacion',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_estud = fields.Integer(
        string='Estudio',
        default=0,
        groups='hr.group_hr_user'
    )

    bono_estud_esp = fields.Integer(
        string='Estudio Especial',
        default=0,
        groups='hr.group_hr_user'
    )

    capac = fields.Html(
        string='Capacitaciones y/o Cursos',
        groups='hr.group_hr_user'
    )

    jornada = fields.Selection([
        ('completa', 'Completa'),
        ('parcial', 'Parcial')
    ], 'Jornada Laboral',
       groups='hr.group_hr_user')

    horas = fields.Integer(
        'Horas Semanales',
        groups='hr.group_hr_user'
    )

    banco = fields.Char(
        string='Banco',
        groups='hr.group_hr_user'
    )

    cuenta_banco = fields.Char(
        string='Cuenta',
        groups='hr.group_hr_user'
    )

    cuenta_tipo = fields.Selection([
        ('cc', 'Cuenta Corriente'),
        ('vi', 'Cuenta Vista'),
        ('ah', 'Cuenta Ahorro')
    ], 'Tipo de cuenta',
       groups='hr.group_hr_user')


    ingreso = fields.Date(
        string='Fecha de Incorporación',
        groups='hr.group_hr_user',
    )

    progresivo = fields.Boolean(
        string='Vacaciones Progresivas',
        groups='hr.group_hr_user',
    )

    certi_progre = fields.Date(
        string='Fecha del Certificado',
        groups='hr.group_hr_user',
    )

    periodo = fields.Integer(
        string='Período',
        groups='hr.group_hr_user',
    )

    @api.model
    def _asignar_vacaciones_progresivas(self):
        hoy = fields.Date.context_today(self)

        # Buscar empleados con vacaciones progresivas
        # y fecha de certificado.
        empleados = self.search([
            ('progresivo', '=', True),
            ('certi_progre', '!=', False),
        ])

        for empleado in empleados:

            # Comparar solamente día y mes.
            if (
                empleado.certi_progre.day != hoy.day
                or empleado.certi_progre.month != hoy.month
            ):
                continue

            # Ya procesado durante el año actual.
            if empleado.periodo == hoy.year:
                continue

            # Años completos desde la fecha del certificado.
            anios = relativedelta(
                hoy,
                empleado.certi_progre
            ).years

            # Un día por cada período completo de 3 años.
            dias_progresivos = anios // 3

            if dias_progresivos <= 0:
                continue

            # Buscar la asignación existente del plan de acumulación.
            asignacion = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', empleado.id),
                ('accrual_plan_id', '=', 1),
                ('state', '=', 'validate'),
                ('allocation_type', '=', 'accrual'),
            ], limit=1)

            if not asignacion:
                continue

            # Sumar los días progresivos a la asignación existente.
            asignacion.write({
                'number_of_days': (
                    asignacion.number_of_days + dias_progresivos
                ),
            })

            # Registrar el año de la asignación.
            empleado.write({
                'periodo': hoy.year,
            })