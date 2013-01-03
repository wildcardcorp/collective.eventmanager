import os

from getpaid.wizard.interfaces import IWizard
from plone.directives import dexterity
from plone.directives import form
from zope import schema
from zope.dottedname.resolve import resolve
from zope.interface import Interface

from collective.eventmanager import EventManagerMessageFactory as _


class ILayer(Interface):
    pass


class IEMWizard(IWizard):
    pass


class IRegistrationDefault(form.Schema):
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


IBaseRegistration = IRegistrationDefault
try:
    if 'DEFAULT_REGISTRATION_SCHEMA' in os.environ:
        import pdb; pdb.set_trace()
        IBaseRegistration = resolve(os.environ['DEFAULT_REGISTRATION_SCHEMA'])
except ImportError:
    pass
