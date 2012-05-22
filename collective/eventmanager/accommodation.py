from five import grok
from zope import schema
from plone.directives import form
from Products.CMFCore.utils import getToolByName
from collective.geo.mapwidget.browser.widget import MapWidget
from collective.geo.mapwidget.interfaces import IMapWidget
from collective.z3cform.mapwidget.widget import MapFieldWidget

from collective.eventmanager.interfaces import ILayer
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

#class TravelAccommodationMapWidget()


class View(grok.View):
    """Default view (called "@@view"") for an accommodation.

    The associated template is found in accommodation_templates/view.pt
    """

    grok.context(IAccommodation)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    def __call__(self):
        portal = getToolByName(self.context, "portal_url")
        mw = MapWidget(self, self.request, portal)
        mw.mapid = 'location'
        self.mapfields = [mw]

        import pdb; pdb.set_trace()

        return super(View, self).__call__()
