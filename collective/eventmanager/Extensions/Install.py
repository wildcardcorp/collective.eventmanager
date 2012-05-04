from Products.CMFCore.utils import getToolByName
from collective.eventmanager.config import BASE_TYPE_NAME

_types_add_allowable = (
    'Session',
    'TravelAccommodation',
    'LodgingAccommodation',
    'Registration')


def install(context, reinstall=False):
    types = getToolByName(context, 'portal_types')

    # need to make all the types as addable to a Folder
    folder = types['Folder']
    allowed_content_types = set(folder.allowed_content_types)
    for _type in _types_add_allowable:
        allowed_content_types.add(BASE_TYPE_NAME + _type)
    folder.allowed_content_types = tuple(allowed_content_types)

    ps = getToolByName(context, 'portal_setup')
    ps.runAllImportStepsFromProfile('profile-collective.eventmanager:default')


def uninstall(context, reinstall=False):
    pass
