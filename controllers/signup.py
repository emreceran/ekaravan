# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import werkzeug
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import math

from dateutil.relativedelta import relativedelta
from operator import itemgetter

from odoo import fields, http, modules, tools
from odoo.http import request
from odoo.osv import expression
from odoo.addons.web.controllers import home as web_home



class WebsiteProfile(http.Controller):
    _users_per_page = 30
    _pager_max_pages = 5

    # Profile
    # ---------------------------------------------------

    def _check_avatar_access(self, user_id, **post):
        """ Base condition to see user avatar independently form access rights
        is to see published users having karma, meaning they participated to
        frontend applications like forum or elearning. """
        try:
            user = request.env['res.users'].sudo().browse(user_id).exists()
        except:
            return False
        if user:
            return user.website_published and user.karma > 0
        return False

    def _check_user_profile_access(self, user_id):
        user_sudo = request.env['res.users'].sudo().browse(user_id)
        # User can access - no matter what - his own profile
        if user_sudo.id == request.env.user.id:
            return user_sudo
        if user_sudo.karma == 0 or not user_sudo.website_published or \
            (user_sudo.id != request.session.uid and request.env.user.karma < request.website.karma_profile_min):
            return False
        return user_sudo

    def _prepare_user_values(self, **kwargs):
        kwargs.pop('edit_translations', None) # avoid nuking edit_translations
        values = {
            'user': request.env.user,
            'is_public_user': request.website.is_public_user(),
            'validation_email_sent': request.session.get('validation_email_sent', False),
            'validation_email_done': request.session.get('validation_email_done', False),
        }
        values.update(kwargs)
        return values

    def _prepare_user_profile_parameters(self, **post):
        return post

    def _prepare_user_profile_values(self, user, **post):
        return {
            'uid': request.env.user.id,
            'user': user,
            'main_object': user,
            'is_profile_page': True,
            'edit_button_url_param': '',
        }

    @http.route([
        '/profile/avatar/<int:user_id>',
    ], type='http', auth="public", website=True, sitemap=False)
    def get_user_profile_avatar(self, user_id, field='avatar_256', width=0, height=0, crop=False, **post):
        if field not in ('image_128', 'image_256', 'avatar_128', 'avatar_256'):
            return werkzeug.exceptions.Forbidden()

        if (int(width), int(height)) == (0, 0):
            width, height = tools.image_guess_size_from_field_name(field)

        can_sudo = self._check_avatar_access(int(user_id), **post)
        return request.env['ir.binary']._get_image_stream_from(
            request.env['res.users'].sudo(can_sudo).browse(int(user_id)),
            field_name=field, width=int(width), height=int(height), crop=crop
        ).get_response()

    @http.route(['/profile/user/<int:user_id>'], type='http', auth="public", website=True)
    def view_user_profile(self, user_id, **post):
        user = self._check_user_profile_access(user_id)
        if not user:
            return request.render("website_profile.private_profile")
        values = self._prepare_user_values(**post)
        params = self._prepare_user_profile_parameters(**post)
        values.update(self._prepare_user_profile_values(user, **params))
        return request.render("website_profile.user_profile_main", values)

    # Edit Profile
    # ---------------------------------------------------
    @http.route('/profile/edit', type='http', auth="user", website=True)
    def view_user_profile_edition(self, **kwargs):
        user_id = int(kwargs.get('user_id', 0))
        countries = request.env['res.country'].search([])
        # subeler = request.env['hr.department'].search([])
        subeler = request.env['hr.department'].search([('derece', '=', '1')])
        ilceler = request.env['hr.department'].sudo().search([('derece', '=', '2')])
        okullar = request.env['hr.department'].sudo().search([('derece', '=', '3')])
        if user_id and request.env.user.id != user_id and request.env.user._is_admin():
            user = request.env['res.users'].browse(user_id)
            values = self._prepare_user_values(searches=kwargs, user=user, is_public_user=False)
        else:
            values = self._prepare_user_values(searches=kwargs)
        values.update({
            'email_required': kwargs.get('email_required'),
            'countries': countries,
            'url_param': kwargs.get('url_param'),
            'okullar': okullar,
            'subeler': subeler,
            'ilceler': ilceler,
        })
        print(values)
        return request.render("website_profile.user_profile_edit_main", values)

    def _profile_edition_preprocess_values(self, user, **kwargs):
        values = {
            'name': kwargs.get('name'),
            'website': kwargs.get('website'),
            'email': kwargs.get('email'),
            'city': kwargs.get('city'),
            'country_id': int(kwargs.get('country')) if kwargs.get('country') else False,
            'website_description': kwargs.get('description'),
            'sube': kwargs.get('sube_id'),

        }

        if 'clear_image' in kwargs:
            values['image_1920'] = False
        elif kwargs.get('ufile'):
            image = kwargs.get('ufile').read()
            values['image_1920'] = base64.b64encode(image)

        if request.uid == user.id:  # the controller allows to edit only its own privacy settings; use partner management for other cases
            values['website_published'] = kwargs.get('website_published') == 'True'
        return values




class AuthSignupHome(web_home.Home):

    def _prepare_user_values2(self, **kwargs):
        kwargs.pop('edit_translations', None) # avoid nuking edit_translations
        values = {


            'validation_email_sent': request.session.get('validation_email_sent', False),
            'validation_email_done': request.session.get('validation_email_done', False),
        }
        values.update(kwargs)
        return values

    @http.route('/web/signup', type='http', auth="public", website=True)
    def view_user_profile_edition(self, **kwargs):
        # user_id = int(kwargs.get('user_id', 0))
        # countries = request.env['res.country'].search([])
        # # subeler = request.env['hr.department'].search([])
        # subeler = request.env['hr.department'].search([('derece', '=', '1')])
        # ilceler = request.env['hr.department'].sudo().search([('derece', '=', '2')])
        okullar = request.env['hr.department'].search([('derece', '=', '3')])
        # if user_id and request.env.user.id != user_id and request.env.user._is_admin():
        #     user = request.env['res.users'].browse(user_id)
        #     values = self._prepare_user_values(searches=kwargs, user=user, is_public_user=False)
        # else:
        values = self._prepare_user_values2(searches=kwargs)
        values.update({
            # 'email_required': kwargs.get('email_required'),
            # 'countries': countries,
            # 'url_param': kwargs.get('url_param'),
            'okullar': okullar,
            # 'subeler': subeler,
            # 'ilceler': ilceler,
        })
        # print(values)
        return request.render("auth_signup.signup", values)

    """


    def _signup_with_values(self, token, values):
        context = self.get_auth_signup_qcontext()
        values.update({'street': context.get('street')})
        super(AuthSignupHome, self)._signup_with_values(token, values)

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        response = super(AuthSignupHome, self).web_login(*args, **kw)
        response.qcontext.update(self.get_auth_signup_config())
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            # Redirect if already logged in and redirect param is present
            return request.redirect(request.params.get('redirect'))
        return response

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):


        subeler = request.env['hr.department'].sudo().search([])


        qcontext = super(AuthSignupHome, self).get_auth_signup_qcontext()
        qcontext['subeler'] = subeler
        # qcontext['ilceler'] = ilceler
        # qcontext['okullar'] = okullar
        print(subeler)




        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        # response.headers['X-Frame-Options'] = 'DENY'
        return response
#
#     @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
#     def web_auth_reset_password(self, *args, **kw):
#         qcontext = self.get_auth_signup_qcontext()
#
#         if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
#             raise werkzeug.exceptions.NotFound()
#
#         if 'error' not in qcontext and request.httprequest.method == 'POST':
#             try:
#                 if qcontext.get('token'):
#                     self.do_signup(qcontext)
#                     return self.web_login(*args, **kw)
#                 else:
#                     login = qcontext.get('login')
#                     assert login, _("No login provided.")
#                     _logger.info(
#                         "Password reset attempt for <%s> by user <%s> from %s",
#                         login, request.env.user.login, request.httprequest.remote_addr)
#                     request.env['res.users'].sudo().reset_password(login)
#                     qcontext['message'] = _("An email has been sent with credentials to reset your password")
#             except UserError as e:
#                 qcontext['error'] = e.args[0]
#             except SignupError:
#                 qcontext['error'] = _("Could not reset your password")
#                 _logger.exception('error when resetting password')
#             except Exception as e:
#                 qcontext['error'] = str(e)
#
#         response = request.render('auth_signup.reset_password', qcontext)
#         response.headers['X-Frame-Options'] = 'DENY'
#         return response
#"""
#     def get_auth_signup_config(self):
#         """retrieve the module config (which features are enabled) for the login page"""
#
#         get_param = request.env['ir.config_parameter'].sudo().get_param
#         return {
#             'signup_enabled': request.env['res.users']._get_signup_invitation_scope() == 'b2c',
#             'reset_password_enabled': get_param('auth_signup.reset_password') == 'True',
#         }
#
#     def get_auth_signup_qcontext(self):
#         """ Shared helper returning the rendering context for signup and reset password """
#         qcontext = {k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
#         qcontext.update(self.get_auth_signup_config())
#         if not qcontext.get('token') and request.session.get('auth_signup_token'):
#             qcontext['token'] = request.session.get('auth_signup_token')
#         if qcontext.get('token'):
#             try:
#                 # retrieve the user info (name, login or email) corresponding to a signup token
#                 token_infos = request.env['res.partner'].sudo().signup_retrieve_info(qcontext.get('token'))
#                 for k, v in token_infos.items():
#                     qcontext.setdefault(k, v)
#             except:
#                 qcontext['error'] = _("Invalid signup token")
#                 qcontext['invalid_token'] = True
#         return qcontext
#
#     def _prepare_signup_values(self, qcontext):
#         values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }
#         if not values:
#             raise UserError(_("The form was not properly filled in."))
#         if values.get('password') != qcontext.get('confirm_password'):
#             raise UserError(_("Passwords do not match; please retype them."))
#         supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
#         lang = request.context.get('lang', '')
#         if lang in supported_lang_codes:
#             values['lang'] = lang
#         return values
#
#     def do_signup(self, qcontext):
#         """ Shared helper that creates a res.partner out of a token """
#         values = self._prepare_signup_values(qcontext)
#         self._signup_with_values(qcontext.get('token'), values)
#         request.env.cr.commit()
#
#     def _signup_with_values(self, token, values):
#         db, login, password = request.env['res.users'].sudo().signup(values, token)
#         request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
#         uid = request.session.authenticate(db, login, password)
#         if not uid:
#             raise SignupError(_('Authentication Failed.'))
# #
# # class AuthBaseSetup(BaseSetup):
# #     @http.route('/base_setup/data', type='json', auth='user')
# #     def base_setup_data(self, **kwargs):
# #         res = super().base_setup_data(**kwargs)
# #         res.update({'resend_invitation': True})
# #         return res
