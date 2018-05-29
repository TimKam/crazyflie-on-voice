#!/usr/bin/env python3

# This module provides modelling of obstacles in a scene and path planning to
# avoid those obstacles. Currently, Obstacles can be boxes that are described
# by scaling and translating unit cubes.
#
# Author: Christopher Blöcker

import numpy as np

from src.redblack import *

# functions for tuple projections
fst = lambda p: p[0]
snd = lambda p: p[1]


class Point():
    """
    A 3D point
    """
    def __init__(self, x, y , z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return np.abs(self.x - other.x) <= np.finfo(float).eps \
           and np.abs(self.y - other.y) <= np.finfo(float).eps \
           and np.abs(self.z - other.z) <= np.finfo(float).eps

    def __repr__(self):
        return "({:.2f}, {:.2f}, {:.2f})".format(self.x, self.y, self.z)

    def distanceTo(self, point):
        """
        measures the distance to a given point

        :param point:
        """
        return np.linalg.norm([self.x - point.x, self.y - point.y, self.z - point.z])

    def sub(self, point):
        """

        :param point:
        """
        return Point( self.x - point.x
                    , self.y - point.y
                    , self.z - point.z
                    )


class Object(ABC):
    """
    An abstract object
    """
    def __init__(self):
        pass

    @abstractmethod
    def contains(self, point):
        """
        Checks whether the given point lies within the object.

        :param point:
        :return:
        """
        raise Exception("contains not implemented.")


class Scale(Object):
    """
    Scales an object according to the given scaling factors in x-, y-, and z-direction.
    """
    def __init__(self, scaledObject, scaleX, scaleY, scaleZ):
        self.scaledObject = scaledObject
        self.scaleX       = scaleX
        self.scaleY       = scaleY
        self.scaleZ       = scaleZ

    def contains(self, point):
        """
        Transforms the given point into the coordinate frame of the object and
        checks whether the point lies within the object.

        :param point:
        :return:
        """
        scaledPoint = Point( point.x / self.scaleX
                           , point.y / self.scaleY
                           , point.z / self.scaleZ
                           )

        return self.scaledObject.contains(scaledPoint)


class Translate(Object):
    """
    Translates an object according to the given translations in x-, y-, and z-direction.
    """
    def __init__(self, translatedObject, translateX, translateY, translateZ):
        self.translatedObject = translatedObject
        self.translateX       = translateX
        self.translateY       = translateY
        self.translateZ       = translateZ

    def contains(self, point):
        """
        Translates the given point into the coordinate frame of the object and
        checks whether the point lies within the object.

        :param point:
        :return:
        """
        translatedPoint = Point( point.x - self.translateX
                               , point.y - self.translateY
                               , point.z - self.translateZ
                               )

        return self.translatedObject.contains(translatedPoint)


class Cube(Object):
    """
    A unit cube
    """
    def __init(self):
      Object.__init__(self)

    def contains(self, point):
        """
        The unit cube contains those points which have coordinates between 0 and 1
        in all dimenstions.

        :param point:
        :return: ``True`` or ``False``
        """
        return 0 <= point.x <= 1 \
           and 0 <= point.y <= 1 \
           and 0 <= point.z <= 1


class Scene():
    """
    A scene is represented as a cuboid and contains a set of obstacles that should
    be avoided in path planning. When constructed, the scene is represented as a
    regular cartesian grid according to the given resolution. The space is sampled
    and occupied grid cells are marked.
    """
    def __init__(self, dimX, dimY, dimZ, resolution, obstacles):
      self.resolution = resolution
      self.bounds     = Scale(Cube(), dimX, dimY, dimZ)

      # number of grid cells in each direction
      x = int(dimX / resolution)
      y = int(dimY / resolution)
      z = int(dimZ / resolution)

      # to store which cells are occupied
      self.space = np.zeros((x, y, z))

      # Build the scene according to the given resolution and sample the space to
      # represent it as a 3D array with boolean values where True means that the
      # respective spot is occupied by an obstacle
      for i in range(x):
          for j in range(y):
              for k in range(z):
                  p = Point((i + 0.5) * resolution, (j + 0.5) * resolution, (k + 0.5) * resolution)
                  self.space[i, j, k] = any([obstacle.contains(p) for obstacle in obstacles])

    def getPoint(self, xyz):
        """
        Get the middle of a given grid cell (gx, gy, gz)

        :param xyz:
        :return:
        """
        return Point( (xyz[0] + 0.5) * self.resolution
                    , (xyz[1] + 0.5) * self.resolution
                    , (xyz[2] + 0.5) * self.resolution
                    )

    # Get the coordinate in the grid of a point.
    def getCoordinate(self, point):
        return ( int(point.x  / self.resolution)
               , int(point.y  / self.resolution)
               , int(point.z  / self.resolution)
               )

    def planPath(self, start, target):
        """
        Use A* to plan a path from start to target and avoids the obstacles in the scene.

        :param start:
        :param target:
        :return:
        """
        # the start point must be within the scene
        if not self.bounds.contains(start):
            raise Exception("Start ({:.2f}, {:.2f}, {:.2f}) is out of bounds!".format(start.x, start.y, start.z))

        # the target point must be within the scene
        if not self.bounds.contains(target):
            raise Exception("Target ({:.2f}, {:.2f}, {:.2f}) is out of bounds!".format(target.x, target.y, target.z))

        # the grid cells corresponding to start and target
        startCell  = self.getCoordinate(start)
        targetCell = self.getCoordinate(target)

        # the start point must not lie within an obstacle
        if self.space[startCell[0], startCell[1], startCell[2]]:
            raise Exception("Start {} point lies within an obstacle!".format(self.getPoint(startCell)))

        # the target point must not lie within an obstacle
        if self.space[targetCell[0], targetCell[1], targetCell[2]]:
            raise Exception("Target {} point lies within an obstacle!".format(self.getPoint(startCell)))

        # explored and unexplored cells
        explored   = set()
        unexplored = { startCell : 0 }

        # a queue of cells to retrieve that cell with expected lowest cost
        queue      = Empty(key = snd).insert((startCell, start.distanceTo(target)))

        # for reconstructing the path, stores the predecessor of cells along the cheapest path
        cameFrom   = { startCell : startCell }

        # costs to get to the grid cells
        costs      = { startCell : 0 }

        # continue planning as long as we have unexplored grid cells left
        while len(unexplored) > 0:
            (current, currentCost), queue = queue.popMin()
            while current not in unexplored:
                (current, _), queue = queue.popMin()
            unexplored.pop(current)
            explored.add(current)

            # we found a path!
            if current == targetCell:
                return self.postprocessPath(self.reconstructPath(cameFrom, current, target))

            p = self.getPoint(current)

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    for dz in [-1, 0, 1]:
                        x = current[0] + dx
                        y = current[1] + dy
                        z = current[2] + dz

                        q = self.getPoint((x, y, z))

                        if (x, y, z) not in explored and self.bounds.contains(q) and not self.space[x, y, z]:
                            cost = currentCost + p.distanceTo(q)

                            if (x, y, z) not in unexplored or cost < unexplored[(x, y, z)]:
                                queue = queue.insert(((x, y, z), cost + q.distanceTo(target)))
                                unexplored[(x, y, z)] = cost
                                cameFrom[(x, y, z)]   = current
                                costs[(x, y, z)]      = cost

        raise Exception("Cannot find a path to target!")

    def reconstructPath(self, cameFrom, endpoint, target):
        """

        :param cameFrom:
        :param endpoint:
        :param target:
        :return:
        """
        path = [ target
               , self.getPoint(endpoint)
               ]

        while endpoint != cameFrom[endpoint]:
            endpoint = cameFrom[endpoint]
            path.append(self.getPoint(endpoint))
        return path[::-1]

    def planLanding(self, start):
        """

        :param start:
        :return:
        """
        print("[DEBUG] planning landing...")

        currentCell = self.getCoordinate(start)
        landingPath = [start]
        print("[DEBUG] landing waypoint: {}".format(currentCell))

        # descend
        while not self.space[currentCell[0], currentCell[1], currentCell[2]] and currentCell[2] > 0:
            print("[DEBUG] landing waypoint: {}".format(currentCell))
            currentCell = (currentCell[0], currentCell[1], currentCell[2] - 1)
            landingPath.append(self.getPoint(currentCell))

        return landingPath

    def postprocessPath(self, path):
        """

        :param path:
        :return:
        """
        reducedPath = [path[0]]

        for i in range(1, len(path) - 1):
            if path[i].sub(path[i-1]) != path[i+1].sub(path[i]):
                reducedPath.append(path[i])

        reducedPath.append(path[-1])

        print("[DEBUG] Original path: {}".format(path))
        print("[DEBUG] Reduced path: {}".format(reducedPath))

        return reducedPath


if __name__ == '__main__':
    table1 = Translate(Scale(Cube(), 1.30, 0.65, 0.75), 1.67, 0.00, 0.00)
    table2 = Translate(Scale(Cube(), 1.30, 0.85, 0.60), 1.67, 3.75, 0.00)

    obstacle1 = Translate(Scale(Cube(), 1.5, 0.85, 2.0), 1.55, 1.05, 0.00)
    obstacle2 = Translate(Scale(Cube(), 2.0, 1.15, 2.0), 0.00, 2.10, 0.00)
    obstacle3 = Translate(Scale(Cube(), 1.5, 1.15, 2.0), 2.50, 2.10, 0.00)
    obstacle4 = Translate(Scale(Cube(), 4.0, 1.15, 1.3), 0.00, 2.10, 0.70)

    scene  = Scene(4.0, 5.0, 2.0, 0.1, [table1, table2, obstacle1, obstacle2, obstacle3, obstacle4])
    start  = Point(2.19, 0.36, 1.31)
    target = Point(2.19, 4.16, 1.31)

    path = scene.planPath(start, target)
    print(path)

    pathLength = 0
    i = 1
    while i < len(path):
        pathLength += path[i-1].distanceTo(path[i])
        i += 1
    print(pathLength)

    #landingPath = scene.planLanding(start)
    #print(landingPath)
