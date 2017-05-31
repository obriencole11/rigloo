import pymel.core as pmc


def co_duplicate_skeleton(root, suffix = '_JNT'):
    '''
    Duplicates a skeleton and parent to the world.
    :param root: The root of the source skeleton
    :param suffix: (optional) The suffix to be appended to the joint name
    :return: The root of the copied skeleton
    '''
    def duplicateChild(obj, parent=None):
        newObj = co_duplicate_and_rename(obj, suffix=suffix)
        if parent:
            pmc.parent(newObj, parent)
        for child in obj.listRelatives(c=True):
            duplicateChild(child, parent=newObj)
        return newObj

    newRoot = duplicateChild(root)
    return newRoot


def co_duplicate_and_rename(obj, prefix="", suffix="_DUP"):
    '''
    Duplicates and adds a prefix and/or suffix to the result.
    :param obj: The reference object to be duplicated.
    :param prefix: The prefix string.
    :param suffix: The suffix string.
    :return: The duplicated object.
    '''
    newObj = pmc.duplicate(obj, po=True)
    pmc.rename(newObj, prefix + obj.name() + suffix)
    return newObj[0]


def co_create_connected_skeleton(root, suffix = 'JNT'):
    '''
    Creates a duplicate skeleton in which all transforms
    are connected to the source skeleton.
    :param root: The root of the source skeleton.
    :param suffix: (optional) The suffix to be appended to the joint name
    :return: The root of the connected skeleton.
    '''
    def duplicateChild(obj, parent=None):
        newObj = co_duplicate_and_rename(obj, suffix=suffix)
        co_connect_all_transforms(obj, newObj)
        if parent:
            pmc.parent(newObj, parent)
        for child in obj.listRelatives(c=True):
            duplicateChild(child, parent=newObj)
        return newObj

    newRoot = duplicateChild(root)

    return newRoot


def co_connect_all_transforms(source, destination):
    '''
    Connects all transforms of two objects.
    :param source: The reference transform.
    :param destination: The object to be connected.
    :return: None
    '''
    pmc.connectAttr(source.t, destination.t)
    pmc.connectAttr(source.r, destination.r)
    pmc.connectAttr(source.s, destination.s)


def co_add_prefix(input, prefix):
    '''
    Renames a single or group of transforms and adds a prefix
    :param input: The input transform(s) to be renamed
    :param prefix: The string to append to each 
    :return: None
    '''
    name = input.name()
    newName = prefix + name
    input.rename(newName)


def co_add_suffix(input, suffix):
    '''
    Renames a single or group of transforms and adds a suffix
    :param input: The input transform(s) to be renamed
    :param prefix: The string to append to each 
    :return: None
    '''
    name = input.name()
    newName = name + suffix
    input.rename(newName)


def _rigtooltest():
    '''
    Tests for errors.
    '''
    pmc.newFile(force=True)
    joint1 = pmc.joint()
    joint2 = pmc.joint()
    joint3 = pmc.joint()
    co_duplicate_skeleton(joint1)
    co_create_connected_skeleton(joint1)

