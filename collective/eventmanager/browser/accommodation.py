from five import grok
from Products.CMFCore.utils import getToolByName
from collective.geo.mapwidget.browser.widget import MapWidget
from collective.eventmanager.accommodation import IAccommodation
from collective.eventmanager.interfaces import ILayer


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
        mw.mapid = self.MAP_CSS_CLASS
        mw.addClass(self.MAP_CSS_CLASS)
        self.mapfields = [mw]

        return super(View, self).__call__()

    def cgmapSettings(self):
        settings = {}

        coords = [0, 0]
        if self.context.location != None \
                and self.context.location[0:6] == u'POINT(':
            coords = self.context.location[6:-1].split(' ')

        settings['lon'] = float(coords[0])
        settings['lat'] = float(coords[1])
        settings['zoom'] = 16

        return "cgmap.state['" + self.MAP_CSS_CLASS + "'] = " \
               + str(settings) + ";"
