from zope.component import getMultiAdapter
from plone.portlets.interfaces import IPortletManager
from zope.component import getUtility
from plone.portlets.interfaces import IPortletAssignmentMapping


def install(context):

    if context.readDataFile('collective.eventmanager.txt') is None:
        return

    from Products.PloneGetPaid.browser import portlets as gpportlets

    _getpaid_portlet_types = (
        gpportlets.cart.Assignment,
        gpportlets.buy.Assignment,
        gpportlets.donate.Assignment,
        gpportlets.variableamountdonate.Assignment,
        gpportlets.recurring.Assignment,
        gpportlets.ship.Assignment,
        gpportlets.premium.Assignment)

    # Now do something useful
    site = context.getSite()

    # remove portlets
    column = getUtility(IPortletManager, name="plone.rightcolumn",
                        context=site)
    manager = getMultiAdapter((site, column), IPortletAssignmentMapping)
    for name in manager.keys():
        if type(manager[name]) in _getpaid_portlet_types:
            del manager[name]
