from Products.ZenModel.Device import Device
from Products.ZenRelations.RelSchema import ToManyCont, ToOne

class SiebelDevice(Device):
    """
    """
    
    meta_type = portal_type = 'SiebelDevice'

    _relations = Device._relations + (
        ('siebelComponents', ToManyCont(ToOne,
            'ZenPacks.community.zenSiebelCRM.SiebelComponent.SiebelComponent',
            'siebelDevice',
            ),
        ),
    )

