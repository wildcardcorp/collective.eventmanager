from zope import schema
from plone.directives import form
from collective.z3cform.mapwidget.widget import MapFieldWidget
from collective.eventmanager import EventManagerMessageFactory as _


class IAccommodation(form.Schema):
    """An accomodation made for traveling"""

    form.widget(location=MapFieldWidget)
    location = schema.TextLine(
            title=_(u"Location"),
            description=_(u"Address that will be automatically linked to a "
                          u"map"),
            required=False,
        )

    locationDescription = schema.Text(
            title=_(u"Description of Location"),
            description=_(u"A short description of the location"),
            required=False,
        )
