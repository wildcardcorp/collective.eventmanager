import string

from five import grok
from zope import schema
from plone.directives import form
from Products.CMFCore.utils import getToolByName
from collective.geo.mapwidget.browser.widget import MapWidget
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


class View(grok.View):
    """Default view (called "@@view"") for an accommodation.

    The associated template is found in accommodation_templates/view.pt
    """

    grok.context(IAccommodation)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    MAP_CSS_CLASS = 'accommodationlocation'

    def __call__(self):
        # setup map widget
        portal = getToolByName(self.context, "portal_url")
        mw = MapWidget(self, self.request, portal)
        mw.mapid = 'accommodationlocation'
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

    def mapwidth(self):
        return 'inherit'

    def mapheight(self):
        return '500px'
