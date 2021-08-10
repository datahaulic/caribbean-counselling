from odoo import fields, models, api,_
import datetime
import calendar
# from datetime import timedelta
# from datetime import datetime
import requests
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)



from odoo.exceptions import UserError


class CustomZoomMeet(models.Model):
    _inherit = 'calendar.event'
    _description = 'Zoom Meet Details'

    topic_name = fields.Char(string='Meet Topic')
    start_time = fields.Datetime(string='Start Date', index=True)
    password = fields.Char(string='Meet Password')
    agenda = fields.Text(string='Meeting Agenda')
    end_date_time = fields.Datetime(string='End Date', index=True)
    create_flag = fields.Boolean('Flag', default=False)
    meet_flag = fields.Boolean('Add Zoom Meet', default=False)

    meet_url = fields.Text(string='Meet URL')
    meet_id = fields.Text(string='Meet ID')
    meet_pwd = fields.Text(string='Meet Password')
    meet_data = fields.Text(string='Meet DATA', readonly=True)

    def create_attendees(self):
        current_user = self.env.user
        result = {}
        for meeting in self:
            alreay_meeting_partners = meeting.attendee_ids.mapped('partner_id')
            meeting_attendees = self.env['calendar.attendee']
            meeting_partners = self.env['res.partner']
            for partner in meeting.partner_ids.filtered(lambda partner: partner not in alreay_meeting_partners):
                values = {
                    'partner_id': partner.id,
                    'email': partner.email,
                    'event_id': meeting.id,
                }

                if self._context.get('google_internal_event_id', False):
                    values['google_internal_event_id'] = self._context.get('google_internal_event_id')

                # current user don't have to accept his own meeting
                if partner == self.env.user.partner_id:
                    values['state'] = 'accepted'

                attendee = self.env['calendar.attendee'].create(values)

                meeting_attendees |= attendee
                meeting_partners |= partner

            # if meeting_attendees and not self._context.get('detaching'):
            #     to_notify = meeting_attendees.filtered(lambda a: a.email != current_user.email)
            #     to_notify._send_mail_to_attendees('calendar.calendar_template_meeting_invitation')

            if meeting_attendees:
                meeting.write({'attendee_ids': [(4, meeting_attendee.id) for meeting_attendee in meeting_attendees]})

            if meeting_partners:
                meeting.message_subscribe(partner_ids=meeting_partners.ids)

            # We remove old attendees who are not in partner_ids now.
            all_partners = meeting.partner_ids
            all_partner_attendees = meeting.attendee_ids.mapped('partner_id')
            old_attendees = meeting.attendee_ids
            partners_to_remove = all_partner_attendees + meeting_partners - all_partners

            attendees_to_remove = self.env["calendar.attendee"]
            if partners_to_remove:
                attendees_to_remove = self.env["calendar.attendee"].search(
                    [('partner_id', 'in', partners_to_remove.ids), ('event_id', '=', meeting.id)])
                attendees_to_remove.unlink()

            result[meeting.id] = {
                'new_attendees': meeting_attendees,
                'old_attendees': old_attendees,
                'removed_attendees': attendees_to_remove,
                'removed_partners': partners_to_remove
            }
        return result

    def action_id_calendar_view(self):
        calendar_view = self.env.ref('calendar.view_calendar_event_calendar')
        action_id = self.env['ir.actions.act_window'].search([('view_id', '=', calendar_view.id)], limit=1).id
        return action_id

    def base_url(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return url

    def db_name(self):
        db_name = self._cr.dbname
        return db_name

    def send_mail_notification_mail(self):
        try:
            _logger.info(_("Inside Send Mail Function : \t"))
            company_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))]).company_id
            template_id = self.env['ir.model.data'].get_object_reference('pragtech_odoo_zoom_meeting_integration',
                                                                         'send_mail_meeting_invitation_template_id_one_two_three')[
                1]
            login_user_id = self.env['res.users'].sudo().search([('id', '=', self._context.get('uid'))], limit=1)
            for i in self.attendee_ids:
                if i.partner_id != login_user_id.partner_id:
                    email_template_obj = i.env['mail.template'].browse(template_id)
                    if template_id:
                        _logger.info(_("Template ID : \t%s\t"%template_id))
                        values = email_template_obj.generate_email(i.id, fields=None)
                        values['mail_server_id'] = company_id.outgoing_server_mail_id.id
                        values['email_from'] = login_user_id.email
                        values['email_to'] = i.email
                        values['recipient_ids'] = False
                        values['message_type'] = "email"
                        values['res_id'] = False
                        values['reply_to'] = False
                        values['author_id'] = self.env['res.users'].browse(request.env.uid).partner_id.id
                        mail_mail_obj = self.env['mail.mail']
                        msg_id = mail_mail_obj.sudo().create(values)
                        if msg_id:
                            mail_mail_obj.sudo().send([msg_id])
        except Exception as e:
            _logger.error(_('Error :%s'%e))

    def post_request_meet(self):
        # print("post_request_meet ",self)
        # print("\n self.meet_url ",self.meet_url)
        url = self.meet_url
        return {
            'type': 'ir.actions.act_url',
            'url': url,
        }

    @api.model
    def create(self, vals_list):
        res = super(CustomZoomMeet, self).create(vals_list)
        user_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))])
        company_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))]).company_id
        if vals_list.get('meet_flag'):
            if user_id.zoom_access_token and user_id.zoom_refresh_token:
                res.post_request_meet_user()
                res.send_mail_notification_mail_user()
            elif company_id.zoom_access_token and company_id.zoom_refresh_token:
                res.post_request_meet_company()
                res.send_mail_notification_mail()
            else:
                raise UserError('Please Authenticate First')
        return res

    # def post_request_meet_main(self):
    #     # print("\n\n\n\npost_request_meet ", self)
    #     # print("\n\n\n Self ",self)
    #     # # print("\n\n val -- ",vals_list)
    #     user_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))])
    #     company_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))]).company_id
    #     if vals_list.get('meet_flag'):
    #         if user_id.zoom_access_token and user_id.zoom_refresh_token:
    #
    #             res.post_request_meet_user()
    #             res.send_mail_notification_mail_user()
    #         elif company_id.zoom_access_token and company_id.zoom_refresh_token:
    #             res.post_request_meet_company()
    #             res.send_mail_notification_mail()
    #         else:
    #             raise UserError('Please Authenticate First')
    #     return res

    def send_mail_notification_mail_user(self):
        try:
            company_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))])
            # print("\n\ncompany_id\t\t", company_id.outgoing_server_mail_id, "\n\n")
            template_id = self.env['ir.model.data'].get_object_reference('pragtech_odoo_zoom_meeting_integration',
                                                                         'send_mail_meeting_invitation_user_template_id')[
                1]
            login_user_id = self.env['res.users'].sudo().search([('id', '=', self._context.get('uid'))], limit=1)
            for i in self.attendee_ids:
                if i.partner_id != login_user_id.partner_id:
                    email_template_obj = i.env['mail.template'].browse(template_id)
                    if template_id:

                        values = email_template_obj.generate_email(i.id, ['subject', 'body_html', 'email_from', 'email_to',
                                                                          'email_cc', 'reply_to', 'scheduled_date',
                                                                          'attachment_ids'])
                        values['mail_server_id'] = company_id.outgoing_server_mail_id.id
                        values['email_from'] = login_user_id.email
                        values['email_to'] = i.email
                        values['recipient_ids'] = False
                        values['message_type'] = "email"
                        values['res_id'] = False
                        values['reply_to'] = False
                        values['author_id'] = self.env['res.users'].browse(request.env.uid).partner_id.id
                        mail_mail_obj = self.env['mail.mail']
                        msg_id = mail_mail_obj.sudo().create(values)
                        if msg_id:
                            mail_mail_obj.sudo().send([msg_id])
            return True
        except Exception as e:
            _logger.info(_('Error : %s'%e))

    def post_request_meet_user(self):
        user_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))])
        if self.env.user:
            self.env.user.refresh_token_from_access_token()

        if user_id.zoom_access_token and user_id.zoom_refresh_token:

            zoom_access_token = user_id.sanitize_data(user_id.zoom_access_token)

            bearer = 'Bearer ' + zoom_access_token
            payload = {}
            headers = {
                'Content-Type': "application/json",
                'Authorization': bearer
            }

            st_time = self.start
            start_time = str(st_time).replace(' ', 'T') + 'Z'

            # ed_time = self.start_datetime
            ed_time = self.end_date_time
            end_time = str(ed_time).replace(' ', 'T') + 'Z'

            data = {
                "topic": self.name,
                "type": "2",
                "start_time": start_time,
                "duration": "4",
                "timezone": "NA",
                "password": self.password,
                "agenda": self.description,
                "recurrence": {
                    "type": "2",
                    "repeat_interval": "3",
                    "end_times": "5",
                    "end_date_time": end_time
                },
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "registrants_email_notification": True

                }
            }

            # print("\n\n Before Request : ",json.dumps(data),"\n")
            meet_response = requests.request("POST", "https://api.zoom.us/v2/users/me/meetings", headers=headers,
                                             json=data)
            # print("\n\n Meet Response : ",meet_response,"\nText: ",meet_response.text,"\nStatus: ",meet_response.status_code)

            if meet_response.status_code == 200 or meet_response.status_code == 201:
                data_rec = meet_response.json()
                self.write({"meet_url": data_rec.get('join_url'), "meet_id": data_rec.get('id'),
                            "meet_pwd": data_rec.get('password'), "create_flag": True, "meet_data": data_rec})

            elif meet_response.status_code == 401:
                raise UserError("Please Authenticate with Zoom Meet.")

    def post_request_meet_company(self):
        company_id = self.env['res.users'].search([('id', '=', self._context.get('uid'))]).company_id
        if self.env.user.company_id:
            self.env.user.company_id.refresh_token_from_access_token()

        if company_id.zoom_access_token and company_id.zoom_refresh_token:

            zoom_access_token = company_id.sanitize_data(company_id.zoom_access_token)

            bearer = 'Bearer ' + zoom_access_token
            payload = {}
            headers = {
                'Content-Type': "application/json",
                'Authorization': bearer
            }

            st_time = self.start
            # print("start_time,", st_time)
            start_time = str(st_time).replace(' ', 'T') + 'Z'

            # ed_time = self.start_datetime
            ed_time = self.end_date_time
            # print("end_time,", ed_time, self.duration)
            end_time = str(ed_time).replace(' ', 'T') + 'Z'
            duration = self.duration * 60
            data = {
                "topic": self.name,
                "type": "2",
                "start_time": start_time,
                "duration": duration,
                "timezone": "NA",
                "password": self.password,
                "agenda": self.description,
                "recurrence": {
                    "type": "2",
                    "repeat_interval": "3",
                    "end_times": "5",
                    "end_date_time": end_time
                },
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "registrants_email_notification": True

                }
            }
            # print("\n\nTO BE POST DATA : ", data)
            meet_response = requests.request("POST", "https://api.zoom.us/v2/users/me/meetings", headers=headers,
                                             json=data)
            # print("\n\n Meet Response : ",meet_response,"\nText: ",meet_response.text,"\nStatus: ",meet_response.status_code)
            if meet_response.status_code == 200 or meet_response.status_code == 201:
                data_rec = meet_response.json()
                self.write({"meet_url": data_rec.get('join_url'), "meet_id": data_rec.get('id'),
                            "meet_pwd": data_rec.get('password'), "create_flag": True, "meet_data": data_rec})

            elif meet_response.status_code == 401:
                raise UserError("Please Authenticate with Zoom Meet.")
