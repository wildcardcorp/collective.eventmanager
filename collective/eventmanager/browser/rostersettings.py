from persistent.dict import PersistentDict
from zope.annotation.interfaces import IAnnotations


class RosterSettings(object):
    use_interface = None

    def __init__(self, context, interface):
        self.use_interface = interface
        self.context = context
        annotations = IAnnotations(self.context)

        self._metadata = annotations.get('collective.eventmanager', None)
        if self._metadata is None:
            self._metadata = PersistentDict()
            annotations['collective.eventmanager'] = self._metadata

    def __setattr__(self, name, value):
        if name[0] == '_' or name in ['context', 'use_interface']:
            self.__dict__[name] = value
        else:
            self._metadata[name] = value

    def __getattr__(self, name):
        default = None
        if name in self.use_interface.names():
            default = self.use_interface[name].default

        return self._metadata.get(name, default)
