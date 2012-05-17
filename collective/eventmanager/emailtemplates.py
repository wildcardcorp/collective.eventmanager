from zope.interface import Interface
from zope import schema
from collective.eventmanager import EventManagerMessageFactory as _
from plone.app.registry.browser import controlpanel


class IEMailTemplateSettings(Interface):
    announcement_subject = schema.TextLine(title=u"Announcement Subject")
    announcement_htmlbody = schema.Text(title=u"HTML Body")
    announcement_textbody = schema.Text(title=u"Plain Text Body")

    confirmation_subject = schema.TextLine(title=u"Confirmation Subject")
    confirmation_htmlbody = schema.Text(title=u"Confirmation HTML Body")
    confirmation_textbody = schema.Text(title=u"Confirmation Plain Text Body")

    onwaitinglist_subject = schema.TextLine(title=u"On waiting list Subject")
    onwaitinglist_htmlbody = schema.Text(title=u"On waiting list HTML Body")
    onwaitinglist_textbody = schema.Text(
        title=u"On waiting list Plain Text Body")

    other_subject = schema.TextLine(title=u"Other Subject")
    other_htmlbody = schema.Text(title=u"Other HTML Body")
    other_textbody = schema.Text(title=u"Other Plain Text Body")

    registrationfull_subject = schema.TextLine(
        title=u"Registraion full Subject")
    registrationfull_htmlbody = schema.Text(
        title=u"Registraion full HTML Body")
    registrationfull_textbody = schema.Text(
        title=u"Registraion full Plain Text Body")

    thankyou_subject = schema.TextLine(title=u"Thank you Subject")
    thankyou_htmlbody = schema.Text(title=u"Thank you HTML Body")
    thankyou_textbody = schema.Text(title=u"Thank you Plain Text Body")

    thankyou_with_confirmation_subject = schema.TextLine(
        title=u"Thank you with confirmation Subject")
    thankyou_with_confirmation_htmlbody = schema.Text(
        title=u"Thank you with confirmation HTML Body")
    thankyou_with_confirmation_textbody = schema.Text(
        title=u"Thank you with confirmation Plain Text Body")


class EmailTemplateEditForm(controlpanel.RegistryEditForm):
    schema = IEMailTemplateSettings
    label = u'Event Manager Email Template Settings'


class EmailTemplateConfiglet(controlpanel.ControlPanelFormWrapper):
    form = EmailTemplateEditForm
