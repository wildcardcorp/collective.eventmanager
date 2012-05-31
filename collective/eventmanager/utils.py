from Products.CMFCore.utils import getToolByName


def findRegistrationObject(context):
    """
    context must be an event
    """
    mt = getToolByName(context, 'portal_membership')
    if mt.isAnonymousUser():
        return False
    # XXX should be optimized
    member = mt.getAuthenticatedMember()
    username = member.getUserName()
    registrationfolder = context.registrations
    for reg in registrationfolder.objectValues():
        if reg.email == username:
            return reg


def getNumApprovedAndConfirmed(context):
    if context.portal_type == 'collective.eventmanager.Registration':
        context = context.__parent__
    catalog = getToolByName(context, 'portal_catalog')
    return len(catalog(
        path={'query': '/'.join(context.getPhysicalPath()),
              'depth': 1},
        portal_type='collective.eventmanager.Registration',
        review_state=('approved', 'confirmed')))
