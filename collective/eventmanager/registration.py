from zope import schema
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from plone.directives import form, dexterity
from collective.eventmanager import EventManagerMessageFactory as _


class IRegistration(form.Schema):
    """A registration for an event"""

    title = schema.TextLine(title=_(u"Name"))
    # XXX email WILL be treated as the username
    # XXX this is what connects the registration object
    # XXX to the user.
    email = schema.TextLine(title=_(u"EMail Address"))

    form.mode(for_current_user='hidden')
    dexterity.write_permission(
            noshow='collective.eventmanager.ManageRegistrations')
    noshow = schema.Bool(
                title=_(u"No Show"),
                default=False,
                description=_(u"Set if the registration did not show at the "
                              u"event"))

    dexterity.write_permission(
        paid_fee='collective.eventmanager.ManageRegistrations')
    paid_fee = schema.Bool(
        title=_(u"Paid"),
        description=_(u"Paid registration fee."))

    form.mode(for_current_user='hidden')
    for_current_user = schema.TextLine(
        title=u"For current user", default=u'no')


@form.validator(field=IRegistration['email'])
def validateEmail(value):
    registration = getToolByName(getSite(), 'portal_registration')
    if not registration.isValidEmail(value):
        raise schema.ValidationError("Invalid email address")
