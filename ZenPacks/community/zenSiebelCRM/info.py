from ZenPacks.community.ConstructionKit.ClassHelper import *

def SiebelComponentgetEventClassesVocabulary(context):
    return SimpleVocabulary.fromValues(context.listgetEventClasses())

class SiebelComponentInfo(ClassHelper.SiebelComponentInfo):
    ''''''

from ZenPacks.community.zenSiebelCRM.datasources.SiebelComponentDataSource import *
def SiebelComponentRedirectVocabulary(context):
    return SimpleVocabulary.fromValues(SiebelComponentDataSource.onRedirectOptions)

class SiebelComponentDataSourceInfo(ClassHelper.SiebelComponentDataSourceInfo):
    ''''''


