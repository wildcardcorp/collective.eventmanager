from Solgema.fullcalendar.browser.adapters import TopicEventSource
from Solgema.fullcalendar.interfaces import IEventSource
from collective.eventmanager.interfaces import ILayer
from zope.interface import implements
from zope.component import adapts
from Products.ATContentTypes.interface import IATTopic
from Products.ATContentTypes.lib.calendarsupport import (
    ICS_EVENT_END, rfc2445dt, vformat, ICS_EVENT_START, foldLine)
from StringIO import StringIO
from DateTime import DateTime
from collective.eventmanager.event import IEMEvent
from collective.eventmanager.session import ISession
from Acquisition import aq_base
from plone.uuid.interfaces import IUUID


class EMEventSupport(TopicEventSource):
    implements(IEventSource)
    adapts(IATTopic, ILayer)

    def emGetICal(self, obj):
        """get iCal data
        """
        out = StringIO()
        map = {
            'dtstamp': rfc2445dt(DateTime()),
            'created': rfc2445dt(DateTime(obj.CreationDate())),
            'uid': IUUID(obj),
            'modified': rfc2445dt(DateTime(obj.ModificationDate())),
            'summary': vformat(obj.title),
            'startdate': rfc2445dt(DateTime(obj.start)),
            'enddate': rfc2445dt(DateTime(obj.end)),
            }
        out.write(ICS_EVENT_START % map)

        description = obj.description
        if description:
            out.write(foldLine('DESCRIPTION:%s\n' % vformat(description)))

        location = obj.location
        if location:
            out.write('LOCATION:%s\n' % vformat(location))

        url = obj.absolute_url()
        if url:
            out.write('URL:%s\n' % url)

        out.write(ICS_EVENT_END)
        return out.getvalue()

    def getICal(self):
        args, filters = self._getCriteriaArgs()
        brains = self._getBrains(args, filters)
        results = []
        for brain in brains:
            obj = brain.getObject()
            if IEMEvent.providedBy(obj) or ISession.providedBy(obj):
                results.append(self.emGetICal(obj))
            elif hasattr(aq_base(obj), 'getICal'):
                results.append(obj.getICal())

        return ''.join(results)
