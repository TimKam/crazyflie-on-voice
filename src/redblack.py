#!/usr/bin/env python3

# A (limited, unconventional) red black tree implementation.
# The red black tree can store more complicated data types than in usual
# implementations. We take a function to calculate the "size" of an element
# and insert it into the tree. Because we do that, we can associate additional
# data with an element.
#
# Implemented functionality is insert, retrieving the minimum element, and
# balancing (though the balancing might be incorrect).
#
# Author: Christopher Blöcker

from abc import ABC, abstractmethod

# the identity function
identity = lambda x: x

# Colours to label the nodes.
class Colour():
    BLACK = 0
    RED   = 1


# The interface for a red black tree.
class RedBlackTree(ABC):
    def __init__(self):
        pass

    # Red nodes must not have red children and the number of black nodes along
    # all paths to the leaves must be the same.
    @abstractmethod
    def checkInvariant(self):
        raise Exception("checkInvariant not implemented.")

    # checks whether the tree is empty
    @abstractmethod
    def isEmpty(self):
        raise Exception("isEmpty not implemented.")

    # checks whether the root node is red
    def isRed(self):
        return self.colour == Colour.RED

    # checks whether the root node is black
    def isBlack(self):
        return self.colour == Colour.BLACK

    # counts the number of elements in the tree
    @abstractmethod
    def size(self):
        raise Exception("size not implemented.")

    # inserts an element into the tree and uses the key to measure the element
    @abstractmethod
    def insert(self, element, key = identity):
        raise Exception("insert not implemented.")

    # balances the tree
    @abstractmethod
    def balance(self):
        raise Exception("balance not implemented.")

    # determines the depth of the tree
    @abstractmethod
    def depth(self):
        raise Exception("depth not implemented.")

    # Counts the number of black nodes to the leaf nodes. In a balances tree,
    # there should be the same number of black nodes along all paths from the
    # root to any of the leaves.
    @abstractmethod
    def blackDepth(self):
        raise Exception("blackDepth not implemented.")

    # returns the minimum element and the new tree with the minimum removed
    # the minimum element is always in the leftmost leaf.
    # O(log(n))
    @abstractmethod
    def popMin(self):
        raise Exception("popMin not implemented.")


# An empty red black tree.
# Takes a key function at creation time that is used to "measure" the elements
# for insertion later. Empty nodes are black.
class Empty(RedBlackTree):
    def __init__(self, key = identity):
        RedBlackTree.__init__(self)
        self.key    = key
        self.colour = Colour.BLACK

    def __repr__(self):
        return "<Empty>"

    # Red nodes must not have red children and the number of black nodes along
    # all paths to the leaves must be the same.
    def checkInvariant(self):
        return True

    # checks whether the tree is empty
    def isEmpty(self):
        return True

    # counts the number of elements in the tree
    def size(self):
        return 0

    # hack to fit how the non-empty tree works
    def __insert__(self, element):
        return self.insert(element)

    # inserts an element into the tree and uses the key to measure the element
    def insert(self, element):
        return Node( element = element
                   , colour  = Colour.RED
                   , key     = self.key
                   )

    # balances the tree
    def balance(self):
        return self

    # determines the depth of the tree
    def depth(self):
        return 0

    # Counts the number of black nodes to the leaf nodes. In a balances tree,
    # there should be the same number of black nodes along all paths from the
    # root to any of the leaves.
    def blackDepth(self):
        return 1 if self.isBlack() else 0

    def popMin(self):
        raise Exception("Empty tree!")


# A red black tree that contains data and children.
class Node(RedBlackTree):
    def __init__(self, element, colour = Colour.BLACK, key = identity, left = None, right = None):
        RedBlackTree.__init__(self)
        self.element = element
        self.colour  = colour
        self.key     = key
        self.left    = left  if left  else Empty(key)
        self.right   = right if right else Empty(key)

    def __repr__(self):
        return "(<Node:{}:{}> {} {})".format(self.colour, self.element, self.left, self.right)

    # Red nodes must not have red children and the number of black nodes along
    # all paths to the leaves must be the same.
    def checkInvariant(self):
        return (self.isBlack() or (self.left.isBlack() and self.right.isBlack())) \
           and self.left.checkInvariant() and self.right.checkInvariant() \
           and self.left.blackDepth() == self.right.blackDepth()

    # checks whether the tree is empty
    def isEmpty(self):
        return False

    # counts the number of elements in the tree
    def size(self):
        return 1 + self.left.size() + self.right.size()

    # "internal" method to insert a new element into the tree.
    # Performs rotations to balance the tree if necessary.
    def __insert__(self, element):
        if self.key(element) <= self.key(self.element):
            t = Node( element = self.element
                    , key     = self.key
                    , left    = self.left.__insert__(element)
                    , right   = self.right
                    )
        else:
            t = Node( element = self.element
                    , key     = self.key
                    , left    = self.left
                    , right   = self.right.__insert__(element)
                    )

        if self.isBlack():
            t = t.balance()
        else:
            t.colour = Colour.RED

        return t

    # Inserts an element into the tree. The actual insert is done by __insert__,
    # but we use this wrapper to colour the root node black after insertion.
    def insert(self, element):
        t        = self.__insert__(element)
        t.colour = Colour.BLACK
        return t

    # makes the root node red if it is not already red.
    def mkRed(self):
        if self.colour == Colour.RED:
            raise Exception("This node was already RED!")

        return Node( element = self.element
                   , colour  = Colour.RED
                   , key     = self.key
                   , left    = self.left
                   , right   = self.right
                   )

    # balances the tree
    def balance(self):
        if self.left.isRed() and self.right.isRed():
            t = Node( element = self.element
                    , colour  = Colour.RED
                    , key     = self.key
                    , left    = Node( element = self.left.element
                                    , key     = self.key
                                    , left    = self.left.left
                                    , right   = self.left.right
                                    )
                    , right   = Node( element = self.right.element
                                    , key     = self.key
                                    , left    = self.right.left
                                    , right   = self.right.right
                                    )
                    )

        elif self.left.isRed() and self.left.left.isRed():
            t = Node( element = self.left.element
                    , colour  = Colour.RED
                    , key     = self.key
                    , left    = Node( element = self.left.left.element
                                    , key     = self.key
                                    , left    = self.left.left.left
                                    , right   = self.left.left.right
                                    )
                    , right   = Node( element = self.element
                                    , key     = self.key
                                    , left    = self.left.right
                                    , right   = self.right
                                    )
                    )

        elif self.left.isRed() and self.left.right.isRed():
            t = Node( element = self.left.right.element
                    , colour  = Colour.RED
                    , key     = self.key
                    , left    = Node( element = self.left.element
                                    , key     = self.key
                                    , left    = self.left.left
                                    , right   = self.left.right.left
                                    )
                    , right   = Node( element = self.element
                                    , key     = self.key
                                    , left    = self.left.right.right
                                    , right   = self.right
                                    )
                    )

        elif self.right.isRed() and self.right.right.isRed():
            t = Node( element = self.right.element
                    , colour  = Colour.RED
                    , key     = self.key
                    , left    = Node( element = self.element
                                    , key     = self.key
                                    , left    = self.left
                                    , right   = self.right.left
                                    )
                    , right   = Node( element = self.right.right.element
                                    , key     = self.key
                                    , left    = self.right.right.left
                                    , right   = self.right.right.right
                                    )
                    )

        elif self.right.isRed() and self.right.left.isRed():
            t = Node( element = self.right.left.element
                    , colour  = Colour.RED
                    , key     = self.key
                    , left    = Node( element = self.element
                                    , key     = self.key
                                    , left    = self.left
                                    , right   = self.right.left.left
                                    )
                    , right   = Node( element = self.right.element
                                    , key     = self.key
                                    , left    = self.right.left.right
                                    , right   = self.right.right
                                    )
                    )

        else:
            t = Node( element = self.element
                    , key     = self.key
                    , left    = self.left
                    , right   = self.right
                    )

        return t

    # determines the depth of the tree
    def depth(self):
        return 1 + min(self.left.depth(), self.right.depth())

    # Counts the number of black nodes to the leaf nodes. In a balances tree,
    # there should be the same number of black nodes along all paths from the
    # root to any of the leaves.
    def blackDepth(self):
        l = self.left.blackDepth()
        r = self.right.blackDepth()

        return max(l, r) + (1 if self.isBlack() else 0)

    # "internal" method to find the minimum of the tree and to remove it.
    def __popMin__(self):
        if self.left.isEmpty():
            return (self.element, self.right)

        (m, l) = self.left.__popMin__()

        t = Node( element = self.element
                , colour  = self.colour
                , key     = self.key
                , left    = l
                , right   = self.right
                ).balance()

        return (m, t)

    # returns the minimum element and the new tree with the minimum removed
    # the minimum element is always in the leftmost leaf of the tree.
    # O(log(n))
    def popMin(self):
        (m, t) = self.__popMin__()

        t.colour = Colour.BLACK

        return (m, t)
        # ToDo: we SHOULD check whether the invariant holds after removing
        #       something from the tree... but at the moment it doesn't...
        #       we need to change how we balance the tree after removing something

        # if t.checkInvariant():
        #     return (m, t)
        # else:
        #     print(t)
        #     raise Exception("Malformed tree!")

    # for testing whether popMin returns the correct result
    def getMin(self):
        if self.left.isEmpty() and self.right.isEmpty():
            return self.key(self.element)

        if self.left.isEmpty():
            return min(self.key(self.element), self.right.getMin())

        if self.right.isEmpty():
            return min(self.key(self.element), self.left.getMin())

        return min([self.key(self.element), self.left.getMin(), self.right.getMin()])


if __name__ == '__main__':
    from random import randint, random

    l = [randint(0, 10) for _ in range(1000)]
    t = Empty()

    for x in l:
        t = t.insert(x)

    t.checkInvariant()

    while not t.isEmpty():
        shouldBeMin = t.getMin()
        m, t = t.popMin()

        if m != shouldBeMin:
            raise Exception("Wrong minimum, should be {} but is {}!".format(shouldBeMin, m))
