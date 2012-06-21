from Products.CMFCore.utils import getToolByName
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
