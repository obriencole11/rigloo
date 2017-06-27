import pymel.core as pmc

def generate(skeleton):

    joints = pmc.listRelatives(skeleton, ad=True)
    joints.append(skeleton)

    parents = [joint.getParent() for joint in joints]

    dups = [pmc.duplicate(joint, parentOnly=True, name=joint.name() + '_leafParent')[0] for joint in joints]

    for dup in dups:
        pass

    for index in range(len(joints)):

        pmc.parent(joints[index], dups[index])

    for index in range(len(joints)):

        try:
            pmc.parent(dups[index], dups[joints.index(parents[index])])
        except ValueError:
            pass






selection = pmc.selected()
generate(selection[0])