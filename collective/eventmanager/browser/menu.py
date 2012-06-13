from AccessControl import getSecurityManager
from Products.CMFCore import permissions
from plone.memoize.instance import memoize
from zope.interface import implements

from plone.app.contentmenu import PloneMessageFactory as _
from plone.app.contentmenu.interfaces import IActionsMenu
from plone.app.contentmenu.interfaces import IActionsSubMenuItem

from zope.browsermenu.menu import BrowserMenu
from zope.browsermenu.menu import BrowserSubMenuItem

from collective.eventmanager.event import IEMEvent


class SubMenuItem(BrowserSubMenuItem):
    implements(IActionsSubMenuItem)

    title = _(u'label_actions_menu', default=u'Event Manager')
    description = _(u'title_actions_menu',
        default=u'Actions for event manager')
    submenuId = 'plone_contentmenu_em'

    order = 0
    extra = {'id': 'plone-contentmenu-em'}

    def __init__(self, context, request):
        BrowserSubMenuItem.__init__(self, context, request)

    @property
    def action(self):
        return self.context.absolute_url()

    @memoize
    def available(self):
        return IEMEvent.providedBy(self.context)

    def selected(self):
        return False


class Menu(BrowserMenu):
    implements(IActionsMenu)

    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        if not getSecurityManager().checkPermission(
                permissions.ModifyPortalContent, context):
            return []
        base_url = context.absolute_url()
        return [{
            'title': 'Email Sender',
            'action': "%s/@@emailsenderform" % base_url,
            'description': '',
            'selected': False,
            'icon': '',
            'extra': {'id': 'emailsender', 'separator': None, 'class': ''},
            'submenu': None
        }, {
            'title': 'Registration Status',
            'action': "%s/@@registrationstatusform" % base_url,
            'description': '',
            'selected': False,
            'icon': '',
            'extra': {'id': 'regstatus', 'separator': None, 'class': ''},
            'submenu': None
        }, {
            'title': 'Export Registrations',
            'action': "%s/@@export-registrations" % base_url,
            'description': '',
            'selected': False,
            'icon': '',
            'extra': {'id': 'exportreg', 'separator': None, 'class': ''},
            'submenu': None
        }, {
            'title': 'Add Registrant',
            'action': "%s/registrations/++add++collective.eventmanager.Registration" % base_url,
            'description': '',
            'selected': False,
            'icon': '',
            'extra': {'id': 'addreg', 'separator': None, 'class': ''},
            'submenu': None
        }, {
            'title': 'Roster',
            'action': "%s/@@eventroster" % base_url,
            'description': '',
            'selected': False,
            'icon': '',
            'extra': {'id': 'roster', 'separator': None, 'class': ''},
            'submenu': None
        }]
