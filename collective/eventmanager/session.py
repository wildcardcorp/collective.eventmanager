import string

from five import grok
from zope import schema
from plone.directives import form
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarMarker
from datetime import datetime
from Products.CMFCore.utils import getToolByName
from collective.geo.mapwidget.browser.widget import MapWidget
from collective.z3cform.mapwidget.widget import MapFieldWidget

from collective.eventmanager.interfaces import ILayer
from collective.eventmanager import EventManagerMessageFactory as _


class ISession(form.Schema, ISolgemaFullcalendarMarker):
    """A session within an event"""

    title = schema.TextLine(
            title=_(u"Name of Session"),
            description=_(u"Name of session displayed to users"),
            required=True,
        )

    description = schema.Text(
            title=_(u"Description/Notes"),
            description=_(u"A description or notes about the session"),
            required=False,
        )

    start = schema.Datetime(
            title=_(u"Start Date/Time"),
            description=_(u"Date and time the session starts"),
            required=True,
            default=datetime.today(),
        )

    end = schema.Datetime(
            title=_(u"End Date/Time"),
            description=_(u"Date and time the session ends"),
            required=True,
            default=datetime.today(),
        )

    maxParticipants = schema.Int(
            title=_(u"Maximum Participants"),
            description=_(u"The maximum number of registrants that can "
                          u"participate in this session, if left empty "
                          u"there is no limit"),
            required=False,
        )

    form.widget(location=MapFieldWidget)
    location = schema.TextLine(
            title=_(u"Location"),
            description=_(u"Address of the location of the session"),
            required=False,
        )

    locationDescription = schema.Text(
            title=_(u"Description of Location"),
            description=_(u"A short description of the location"),
            required=False,
        )

    # === CONTACT/PRESENTER DETAILS ===
    contactName = schema.TextLine(
            title=_(u"Contact/Presenter Name"),
            description=_(u"A name for the primary contact or presenter of "
                          u"this event"),
            required=False,
        )

    contactDetails = schema.Text(
            title=_(u"Contact/Presenter Details"),
            description=_(u"Put information about the contact/presentor, "
                          u"including phone, email, twitter handle, and "
                          u"any other descriptive information about the "
                          u"person"),
            required=False,
        )


class View(grok.View):
    """Default view (called "@@view"") for a session.

    The associated template is found in session_templates/view.pt
    """

    grok.context(ISession)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    MAP_CSS_CLASS = 'sessionlocation'

    def __call__(self):
        # setup map widget
        portal = getToolByName(self.context, "portal_url")
        mw = MapWidget(self, self.request, portal)
        mw.mapid = self.MAP_CSS_CLASS
        mw.addClass(self.MAP_CSS_CLASS)
        self.mapfields = [mw]

        return super(View, self).__call__()

    def cgmapSettings(self):
        settings = {}

        coords = [0, 0]
        if self.context.location != None \
                and self.context.location[0:6] == u'POINT(':
            coords = string.split(self.context.location[6:-1], ' ')

        settings['lon'] = float(coords[0])
        settings['lat'] = float(coords[1])
        settings['zoom'] = 16

        return "cgmap.state['" + self.MAP_CSS_CLASS + "'] = " \
               + str(settings) + ";"
