from datetime import datetime
from zope import schema
from plone.directives import form
from plone.app.textfield import RichText
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarMarker
from collective.z3cform.mapwidget.widget import MapFieldWidget

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

    body = RichText(
            title=_(u"Body"),
            description=_(u"This field describes additional content of a "
                          u"session"),
            required=False,
        )

