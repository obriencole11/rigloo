import pymel.core as pmc

def generate(suffix='_LEAF'):

    selection = pmc.selected()[0]

    joints = pmc.listRelatives(selection, ad=True)
    joints.append(selection)

    parents = [joint.getParent() for joint in joints]

    dups = [pmc.duplicate(joint, parentOnly=True, name=joint.name() + suffix)[0] for joint in joints]

    for index in range(len(joints)):


        pmc.parent(joints[index], dups[index])

    for index in range(len(joints)):

        try:
            pmc.parent(dups[index], dups[joints.index(parents[index])])
        except ValueError:
            pass
