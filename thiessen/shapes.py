import fiona

class ShapeFile:

    def __init__(self, file):
        c = fiona.open(file)
        print "hello"

