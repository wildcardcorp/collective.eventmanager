import hashlib
from plone.directives import form, dexterity
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.component.hooks import getSite

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistration(form.Schema):
    """A registration for an event"""

    title = schema.TextLine(title=_(u"Name"))
    email = schema.TextLine(title=_(u"EMail Address"))

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

    form.mode(new_user='hidden')
    new_user = schema.TextLine(
        title=u"new user", default=u'no')


@form.validator(field=IRegistration['email'])
def validateEmail(value):
    registration = getToolByName(getSite(), 'portal_registration')
    if not registration.isValidEmail(value):
        raise schema.ValidationError("Invalid email address")


def generateConfirmationHash(salt, registration):
    msg = "%s%s%s" % (salt, registration.email, registration.getId())
    return hashlib.sha256(msg).hexdigest()
