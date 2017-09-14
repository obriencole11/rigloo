import pymel.core as pmc
import pymel.core.datatypes as dt

def parentConstraint(source, target):

    # Grab the name of the target
    baseName = source.name()

    # Create the required nodes
    multMatrix = pmc.createNode('multMatrix', name=baseName + '_spaceMult')
    decompose = pmc.createNode('decomposeMatrix', name=baseName + '_scaleDecomp')

    # Multiply the targets world matrix by the source's inverse parent matrix
    # This will put the target in the source space
    pmc.connectAttr(source.worldMatrix[0], multMatrix.matrixIn[0])
    pmc.connectAttr(target.parentInverseMatrix[0], multMatrix.matrixIn[1])

    # Connect the result to a decompose matrix to convert to vector values
    pmc.connectAttr(multMatrix.matrixSum, decompose.inputMatrix)

    # Hookup the translate and scale
    pmc.connectAttr(decompose.outputTranslate, target.translate)
    pmc.connectAttr(decompose.outputRotate, target.rotate)

    return [multMatrix, decompose]

def jointConstraint(source, target):

    # Grab the name of the target
    baseName = source.name()

    # Create the required nodes
    parentSpaceMult = pmc.createNode('multMatrix', name=baseName + '_parentSpaceMult')
    jointOrientMult = pmc.createNode('multMatrix', name=baseName + '_jointOrientMult')
    jointOrientCompose = pmc.createNode('composeMatrix', name=baseName + '_jointOrientCompose')
    transposeMatrix = pmc.createNode('transposeMatrix', name=baseName + '_jointOrientInverseMult')
    translateDecompose = pmc.createNode('decomposeMatrix', name=baseName + '_parentSpaceDecomp')
    rotateDecompose = pmc.createNode('decomposeMatrix', name=baseName + '_jointOrientDecomp')

    # Connect the parentspace conversion mult matrix
    # This will bring the source into the target space
    pmc.connectAttr(source.worldMatrix[0], parentSpaceMult.matrixIn[0])
    pmc.connectAttr(target.parentInverseMatrix[0], parentSpaceMult.matrixIn[1])

    # Connect the targets joint orient to the compose matrix's input
    # This will create a matrix from the joint orient
    pmc.connectAttr(target.jointOrient, jointOrientCompose.inputRotate)

    # Connect the Compose matrix to a transpose matrix, this will invert the joint orient
    pmc.connectAttr(jointOrientCompose.outputMatrix, transposeMatrix.inputMatrix)

    # Connect the transpose to the other multiply matrix node
    # This will compensate the parent space switch for the joint orient
    pmc.connectAttr(parentSpaceMult.matrixSum, jointOrientMult.matrixIn[0])
    pmc.connectAttr(transposeMatrix.outputMatrix, jointOrientMult.matrixIn[1])

    # Turn the joint orient matrix mult back into rotation values
    # Then connect it to the target
    pmc.connectAttr(jointOrientMult.matrixSum, rotateDecompose.inputMatrix)
    pmc.connectAttr(rotateDecompose.outputRotate, target.rotate, force=True)

    # Turn the parent space matrix into a translate and scale
    # Input those into the target
    pmc.connectAttr(parentSpaceMult.matrixSum, translateDecompose.inputMatrix, force=True)
    pmc.connectAttr(translateDecompose.outputTranslate, target.translate, force=True)

    return [parentSpaceMult, jointOrientMult, jointOrientCompose, transposeMatrix, translateDecompose, rotateDecompose]

def orientConstraint(source, target):
    pass

def scaleConstraint(source, target):

    # Grab the name of the target
    baseName = source.name()

    # Create the required nodes
    multMatrix = pmc.createNode('multMatrix', name=baseName + '_spaceMult')
    decompose = pmc.createNode('decomposeMatrix', name=baseName + '_decomp')

    # Connect the targets world matrix into the compose matrix
    pmc.connectAttr(source.worldMatrix[0], multMatrix.matrixIn[0])
    pmc.connectAttr(target.parentInverseMatrix[0], multMatrix.matrixIn[1])

    # Connect the result to a decompose matrix to convert to vector values
    pmc.connectAttr(multMatrix.matrixSum, decompose.inputMatrix)

    # Hookup the translate and scale
    pmc.connectAttr(decompose.outputScale, target.scale)

    return [multMatrix, decompose]

def aimTransform(target, aimTarget, upTarget=None):

    # Get the direction to the targetObject
    # This will be the x axis of the final vector
    xVector = target.getTranslation(worldSpace=True) - aimTarget.getTranslation(worldSpace=True)
    xVector.normalize()

    # If there is an upObject specified, use that direction as the upVector
    # Otherwise just use the world up
    if upTarget:
        upDirection = upTarget.getTranslation(worldSpace=True) - aimTarget.getTranslation(worldSpace=True)
        upDirection.normalize()
    else:
        upDirection = dt.VectorN(0, 1, 0)

    # Use cross product to find the vector perpedicular to the xVector and upDirection
    zVector = xVector.cross(upDirection)
    zVector.normalize()

    # Take another cross product to find the final y axis Vector
    yVector = xVector.cross(zVector)
    yVector.normalize()

    # Create the aim Matrix
    aimMatrix = dt.Matrix(xVector.x, xVector.y, xVector.z, 0.0,
                          yVector.x, yVector.y, yVector.z, 0.0,
                          zVector.x, zVector.y, zVector.z, 0.0,
                          0.0, 0.0, 0.0, 1.0)

    # Grab the rotation from that matrix
    rotation = dt.TransformationMatrix(aimMatrix).eulerRotation()

    aimTarget.setRotation(rotation, worldSpace=True)

def aimVector(vector, aimVector, upVector=None):

    # Get the direction to the targetObject
    # This will be the x axis of the final vector
    xVector = vector - aimVector
    xVector.normalize()

    # If there is an upObject specified, use that direction as the upVector
    # Otherwise just use the world up
    if upVector:
        upDirection = upVector - vector
        upDirection.normalize()
    else:
        upDirection = dt.VectorN(0, 1, 0)

    # Use cross product to find the vector perpedicular to the xVector and upDirection
    zVector = xVector.cross(upDirection)
    zVector.normalize()

    # Take another cross product to find the final y axis Vector
    yVector = xVector.cross(zVector)
    yVector.normalize()

    # Create the aim Matrix
    aimMatrix = dt.Matrix(xVector.x, xVector.y, xVector.z, 0.0,
                          yVector.x, yVector.y, yVector.z, 0.0,
                          zVector.x, zVector.y, zVector.z, 0.0,
                          0.0, 0.0, 0.0, 1.0)

    # Grab the rotation from that matrix
    rotation = dt.TransformationMatrix(aimMatrix).eulerRotation()

    return rotation