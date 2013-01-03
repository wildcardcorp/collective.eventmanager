import hashlib

from plone.directives import form
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.component.hooks import getSite
from zope.component.interfaces import IObjectEvent
from zope.interface import Interface

from collective.eventmanager.interfaces import IRegistrationDefault


class IRegistration(IRegistrationDefault):
    pass


@form.validator(field=IRegistration['email'])
def validateEmail(value):
    registration = getToolByName(getSite(), 'portal_registration')
    if not registration.isValidEmail(value):
        raise schema.ValidationError("Invalid email address")


def generateRegistrationHash(salt, registration):
    msg = "%s%s%s" % (salt, registration.email, registration.getId())
    return hashlib.sha256(msg).hexdigest()


class IRegistrationCreatedEvent(IObjectEvent):
    registration = schema.Object(title=u"Registration", schema=IRegistration)


class IRegistrationDefaultSchemaProvider(Interface):
    def getSchema(self):
        """
        Get a schema interface class that defines the default schema for
        a registration.

        @return: zope.interface.Interface that defines a default schema
                 for registrations
        """
