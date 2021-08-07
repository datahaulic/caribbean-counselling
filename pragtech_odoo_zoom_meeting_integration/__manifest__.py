{
    'name': 'Zoom multi user meetings & E-learning connector', # 'Odoo Zoom Meetings Connector Integration',
    'version': '14.0.8',
    'category': 'Other',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'depends': ['calendar', 'web'],
    'summary': 'Odoo Zoom Meetings Connector Integration odoo zoom meetings integration odoo meetings zoom odoo zoom connector zoom integration zoom elerning odoo elearning',
    'description': '''
Pragtech Odoo Zoom Meeting Integration
======================================
This app adds the feature of creating an Odoo meeting with Zoom Meetings as a mode of meeting in Odoo Calendar. This app also adds the feature of joining Zoom Meetings directly from Odoo. Odoo Zoom Meeting Integration allows us to seamlessly schedule meetings in Zoom with Odoo. A meeting in Odoo will automatically be linked into Zoom. A convenient way to work with virtual teams. Now you do not need to separately sign in to Zoom Meetings. Everything happens through Odoo. It is completely secure. You can work with free and paid accounts of Zoom.

Features
--------
	* Any Odoo User can create Meetings
	* Seamless integration between Odoo and Zoom
	* Fully Automated way to schedule meetings
	* Fully SSL secured meetings
	* Zoom Meeting can be password protected
	* Select your Timezone
	* Multi Company and Multi-User Support
	* Works with Enterprise and Community Edition
	* Works with free and Paid Zoom Meetings accounts
	* Backed by our 3 months bugs free support
''',
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/meeting_view.xml',
        'views/res_user_view.xml',
        'views/schedulers.xml',
        'templates/mail_data.xml',
    ],
    'images': ['static/description/odoo-zoom-integration-gif.gif'],
    'live_test_url': 'https://www.pragtech.co.in/company/proposal-form.html?id=103&name=odoo-zoom-integration',
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 129,
    'installable': True,
    'auto_install': False,
}
