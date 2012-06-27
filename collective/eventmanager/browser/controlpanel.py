from plone.app.registry.browser import controlpanel
from collective.eventmanager.emailtemplates import IEMailTemplateSettings
from collective.eventmanager.certificatepdftemplates \
    import ICertificatePDFTemplateSettings


class EmailTemplateEditForm(controlpanel.RegistryEditForm):
    schema = IEMailTemplateSettings
    label = u'Event Manager Email Template Settings'


class EmailTemplateConfiglet(controlpanel.ControlPanelFormWrapper):
    form = EmailTemplateEditForm


class CertificatePDFTemplateEditForm(controlpanel.RegistryEditForm):
    schema = ICertificatePDFTemplateSettings
    label = u'Event Manager Certificate PDF Template Settings'


class CertificatePDFTemplateConfiglet(controlpanel.ControlPanelFormWrapper):
    form = CertificatePDFTemplateEditForm
