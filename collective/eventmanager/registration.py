import hashlib
import os

from plone.directives import form
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.component.hooks import getSite
from zope.component.interfaces import IObjectEvent
from zope.interface import Interface
from zope.dottedname.resolve import resolve
from collective.eventmanager.interfaces import IBaseRegistration

try:
    if 'DEFAULT_REGISTRATION_SCHEMA' in os.environ:
        import pdb; pdb.set_trace()
        IBaseRegistration = resolve(os.environ['DEFAULT_REGISTRATION_SCHEMA'])
except ImportError:
    pass



class IRegistration(IBaseRegistration):
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
