import os
import json
import pymel.core as pmc
import pymel.core.datatypes as dt


CONTROLFILENAME = os.path.join(os.environ['MAYA_APP_DIR'],'control_cache.json')


########## Cache Functions ###############
def load_control_cache():
    '''
    Trys to load the control cache file.
    :return: The newly loaded cache file.
    '''
    try:
        with open(CONTROLFILENAME) as c:
            return json.load(c)
    except IOError:
        return {}


def save_control_cache():
    '''
    Saves the current values of control_shapes to the json cache file.
    '''
    def jdefault(o):
        return o.__dict__

    with open(CONTROLFILENAME, 'w') as c:
        json.dump(control_shapes, c, default=jdefault, indent=4)


def update_control_cache():
    '''
    Checks if the cache file exists, if not, creates one.
    Updates the json file with the latest control_curve values.
    '''
    if not control_cache_exists():
        create_new_control_cache()
    else:
        save_control_cache()


def create_new_control_cache():
    '''
    Overwrites the cache file and replaces with a fresh one.
    :return: 
    '''
    global control_shapes
    new_control_shape = {'default': default_control, 'none': empty_control}
    control_shapes = new_control_shape
    save_control_cache()


def control_cache_exists():
    '''
    This checks if a cache file already exists
    :return: A boolean for the status of the file.
    '''
    return os.path.isfile(CONTROLFILENAME)


########### Curve Functions ##############
class Control():
    '''
    A class to represent a "control" by holding the cv and knot data.
    '''
    def __init__(self, c, k, d):
        self.cvs = c
        self.knots = k
        self.degree = d


def cache_curve(curve, name):
    '''
    Takes a curve and stores the cv and knot information in
    a json file
    :param curve: The curve to cache. 
    :return: The newly created json file
    '''
    curveInfo = get_curve_info(curve)
    control_shapes[name] = curveInfo
    update_control_cache()


def cache_selected_curve(name):
    '''
    Grabs the selection, checks if it is a curve,
    then runs cache_curve on it.
    :param name: The name for the curve
    '''
    selection = pmc.ls(selection = True)
    curve = selection[0].getShapes()
    if curve:
        cache_curve(curve, name)
    else:
        raise Exception('Selection must be a valid curve!')


def remove_curve(name) :
    '''
    Removes a specified curve from the control shapes dict.
    :param name: The name of the curve
    '''
    del control_shapes[name]
    update_control_cache()


def get_curve_info(curve):
    '''
    Returns the cv information and knot information of a curve
    :param curve: The curve to analyze
    :return: The control verts and knots
    '''
    controls = []
    for c in curve:
        cvs = []
        for cv in c.getCVs():
            v = []
            v.append(cv.x)
            v.append(cv.y)
            v.append(cv.z)
            cvs.append(v)
        control = Control(cvs, c.getKnots(), c.degree())
        controls.append(control)
    return controls


def create_control_curve(name):
    '''
    Creates a curve based on input curve info.
    :return: The newly created curve
    '''
    curveInfo = get_control(name)
    parent = pmc.group(em=True)
    for c in curveInfo:
        curve = pmc.curve(p=c.cvs, k=c.knots, d = c.degree)
        pmc.parent(curve.getShape(), parent, shape=True, r=True)
        pmc.delete(curve)
    return parent

def create_control_curve_from_data(data):
    parent = pmc.group(em=True)

    newControl = data
    curveInfo = []
    for c in newControl:
        control = Control(c['cvs'], c['knots'], c['degree'])
        curveInfo.append(control)

    for c in curveInfo:
        curve = pmc.curve(p=c.cvs, k=c.knots, d=c.degree)
        pmc.parent(curve.getShape(), parent, shape=True, r=True)
        pmc.delete(curve)
    return parent

def get_control(name):
    '''
    Returns a cached control if it exists.
    :param controlName: The name of the desired control.
    :return: The curve info of the desired control
    '''
    curves = load_control_cache()
    newControl = curves[name]
    curveInfo = []
    for c in newControl:
        control = Control( c['cvs'], c['knots'],c['degree'] )
        curveInfo.append(control)
    return curveInfo


########## Maya Functions ###############
def freeze_transforms(obj):
    pmc.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True)


def rotate_curve(x, y, z, obj):
    X = 0.0
    Y = 0.0
    Z = 0.0
    if x:
        X = x
    if y:
        Y = y
    if z:
        Z = z
    pmc.rotate(obj, X, Y, Z)


def scale_curve(x, y, z, obj):
    X = 1.0
    Y = 1.0
    Z = 1.0
    if x:
        X = x
    if y:
        Y = y
    if z:
        Z = z
    pmc.scale(obj, X, Y, Z)


def name_curve(name, obj):
    if name == "":
        pmc.rename(obj, "curve")
    else:
        pmc.rename(obj, name)


def move_to_selection(obj):
    selection = pmc.ls(selection = True)
    if selection:
        move_to_transform(obj, selection[0])


def move_to_transform(obj, target, upVector= dt.Vector(0,1,0)):
    ''' 
    Moves an inputed object to a target position.
    Orients to the upVector of the target.
    :param obj: The obj transform to transformed
    :param target: The target transform
    :param upVector: The local up vector of the target
    '''

    # The world up vector
    worldUp = dt.Vector(0, 1, 0)

    # The Transformation matrix of the target in world space
    if target:
        targetSpace = target.getMatrix(worldSpace=True)
    else:
        targetSpace = dt.Matrix()

    # The input upVector transformed into target rotation space
    targetUp = upVector.rotateBy(targetSpace)

    # Create a Quaternion  to represent the rotation
    # From the object orientation to the target orientation
    rotation = worldUp.rotateTo(targetUp)

    # Transform the object into the target space
    obj.setMatrix(targetSpace, worldSpace=True)
    obj.setRotation(rotation, space='world')


default_control = [Control(
    [([0.783611624891, 4.79823734099e-17, -0.783611624891]),
     ([-1.26431706078e-16, 6.78573232311e-17, -1.10819418755]),
     ([-0.783611624891, 4.79823734099e-17, -0.783611624891]),
     ([-1.10819418755, 1.96633546162e-32, -3.21126950724e-16]),
     ([-0.783611624891, -4.79823734099e-17, 0.783611624891]),
     ([-3.33920536359e-16, -6.78573232311e-17, 1.10819418755]),
     ([0.783611624891, -4.79823734099e-17, 0.783611624891]),
     ([1.10819418755, -3.6446300679e-32, 5.95213259928e-16]),
     ([0.783611624891, 4.79823734099e-17, -0.783611624891]),
     ([-1.26431706078e-16, 6.78573232311e-17, -1.10819418755]),
     ([-0.783611624891, 4.79823734099e-17, -0.783611624891])]
    ,
    [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    ,
    3
    )]

empty_control = [Control(
    [
        0.0,
        0.0,
        0.0
    ],
    [
        0.0,
        0.0,
        0.0
    ]
    ,
    3
    )]


control_shapes = load_control_cache()
