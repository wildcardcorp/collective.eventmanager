import zope.interface

from collective.eventmanager.registration import IRegistration
from collective.eventmanager.registration \
    import IRegistrationDefaultSchemaProvider


class RegistrationDefaultSchemaProvider(object):
    zope.interface.implements(IRegistrationDefaultSchemaProvider)

    def __init__(self, context):
        self.context = context

    def getSchema(self):
        return IRegistration
