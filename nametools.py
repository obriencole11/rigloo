class NamingConvention():
    ''' 
    This is a basic class to represent a standard naming convection.
    '''

    def __init__(self, prefix, suffix, useSideNotation=True, rightString='r', leftString='l', centerString='c'):
        self.prefix = prefix
        self.suffix = suffix
        self.useSideNotation = useSideNotation
        self.rightString = rightString
        self.leftString = leftString
        self.centerString = centerString

    # Returns the formatted string using a base string
    # and an string to represent direction
    def getName(self, baseName, side='center', overrideSuffix=None):
        nameArray = [self.prefix, baseName]

        if self.useSideNotation:
            nameArray.append(self.getSide(side))

        if not overrideSuffix == None:
            nameArray.append(overrideSuffix)
        else:
            nameArray.append(self.suffix)

        name = "_".join(nameArray)
        return name

    # Returns the correct directional string
    # based on an input string
    def getSide(self, direction):
        if direction == 'right':
            return  self.rightString
        elif direction == 'center':
            return  self.centerString
        elif direction == 'left':
            return  self.leftString
        else:
            raise TypeError('Direction must be a valid string!')

