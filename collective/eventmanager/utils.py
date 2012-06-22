from Products.CMFCore.utils import getToolByName
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser

from collective.eventmanager.registration import IRegistration


def findRegistrationObject(context, email):
    """
    context must be an event
    """
    catalog = getToolByName(context, 'portal_catalog')
    result = catalog.unrestrictedSearchResults(
        object_provides=IRegistration.__identifier__,
        path={'query': '/'.join(context.getPhysicalPath()),
              'depth': 4},
        email=email)
    if len(result) > 0:
        return result[0]
    return None


def getNumApprovedAndConfirmed(context):
    if context.portal_type == 'collective.eventmanager.Registration':
        context = context.__parent__
    catalog = getToolByName(context, 'portal_catalog')
    return len(catalog(
        path={'query': '/'.join(context.getPhysicalPath()),
              'depth': 1},
        portal_type='collective.eventmanager.Registration',
        review_state=('approved', 'confirmed')))


# http://collective-docs.plone.org/en/latest/security/permissions.html#bypassing-permission-checks
class UnrestrictedUser(BaseUnrestrictedUser):
    def getId(self):
        return self.getUserName()


def executeUnderSpecialRole(portal, role, function, *args, **kwargs):
    sm = getSecurityManager()
    try:
        try:
            tmp_user = UnrestrictedUser(sm.getUser().getId(),
                                        '',
                                        [role],
                                        '')
            tmp_user = tmp_user.__of__(portal.acl_users)
            newSecurityManager(None, tmp_user)

            return function(*args, **kwargs)

        except:
            # special handlers should be run here
            raise
    finally:
        setSecurityManager(sm)
