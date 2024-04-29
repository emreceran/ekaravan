# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import random

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class karavanuser(models.Model):
    _inherit = "res.users"

    sube_id = fields.Many2one("hr.department", string='Şube', ondelete='restrict',
                              )

    ilce_id = fields.Many2one("hr.department", string='İlçe', ondelete='restrict',
                              # related="okul_id.ilce_id"
                              # domain="[('sube_id', '=?', sube_id)]"
                              )

    okul_id = fields.Many2one(
        'hr.department', string='Okul',ondelete='restrict',
        # domain="[('ilce_id', '=?', ilce_id)]"
    )


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    student_answer_image = fields.Binary(string='Student Answer Image', help='Upload an image for the answer')


class department(models.Model):
    _inherit = "hr.department"

    ogrenciler = fields.One2many('res.users', 'okul_id', string='Ogrenciler', readonly=True)
    ilcedekiler = fields.One2many('res.users', 'ilce_id', string='Ogrenciler', readonly=True)
    ildekiler = fields.One2many('res.users', 'sube_id', string='Ogrenciler', readonly=True)



    derece =fields.Selection([
        ('1', 'Sube'),
        ('2', 'İlce'),
        ('3', 'Okul'),
    ],  string="Tip")


    def ogrencileri_goster(self):
        print(self.ogrenciler)

    # def okul_ogrencilerini_listele(self):



