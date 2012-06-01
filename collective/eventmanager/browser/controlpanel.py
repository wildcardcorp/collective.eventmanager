from plone.app.registry.browser import controlpanel
from collective.eventmanager.emailtemplates import IEMailTemplateSettings


class EmailTemplateEditForm(controlpanel.RegistryEditForm):
    schema = IEMailTemplateSettings
    label = u'Event Manager Email Template Settings'


class EmailTemplateConfiglet(controlpanel.ControlPanelFormWrapper):
    form = EmailTemplateEditForm
