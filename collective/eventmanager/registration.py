import hashlib
import os

from plone.directives import form
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.component.hooks import getSite
from zope.component.interfaces import IObjectEvent
from zope.dottedname.resolve import resolve
from collective.eventmanager.interfaces import IBaseRegistration
from logging import getLogger
logger = getLogger('collective.eventmanager')


try:
    if 'DEFAULT_REGISTRATION_SCHEMA' in os.environ:
        #import pdb; pdb.set_trace()
        iface = os.environ['DEFAULT_REGISTRATION_SCHEMA']
        try:
            IBaseRegistration = resolve(iface)
        except AttributeError:
            # if this fails... try different format
            split = iface.split('.')
            base_module = '.'.join(split[:-1])
            __import__(base_module)
            import sys
            IBaseRegistration = getattr(sys.modules[base_module], split[-1])

except ImportError, AttributeError:
    logger.info('error importing base registration')


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
