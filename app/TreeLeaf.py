class TreeLeaf:
    def __init__(self, value=0, child1=False, child2=False):
        if child1 is False and child2 is False:
            self.value = value
        else:
            self.leftChild = child1
            self.rightChild = child2
            self.value = child1.value + child2.value

