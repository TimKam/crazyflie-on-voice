import sys
import numpy as np

class Point():
  def __init__(self, x, y , z):
    self.x = x
    self.y = y
    self.z = z

  def __repr__(self):
    return "({:.2f}, {:.2f}, {:.2f})".format(self.x, self.y, self.z)

  def distanceTo(self, point):
    return np.linalg.norm([self.x - point.x, self.y - point.y, self.z - point.z])


class Object():
  def __init__(self):
    pass

  def contains(self, point):
    return False


class Scale(Object):
  def __init__(self, scaledObject, scaleX, scaleY, scaleZ):
    self.scaledObject = scaledObject
    self.scaleX       = scaleX
    self.scaleY       = scaleY
    self.scaleZ       = scaleZ

  def contains(self, point):
    scaledPoint = Point( point.x / self.scaleX
                       , point.y / self.scaleY
                       , point.z / self.scaleZ
                       )

    return self.scaledObject.contains(scaledPoint)


class Translate(Object):
  def __init__(self, translatedObject, translateX, translateY, translateZ):
    self.translatedObject = translatedObject
    self.translateX       = translateX
    self.translateY       = translateY
    self.translateZ       = translateZ

  def contains(self, point):
    translatedPoint = Point( point.x - self.translateX
                           , point.y - self.translateY
                           , point.z - self.translateZ
                           )

    return self.translatedObject.contains(translatedPoint)


# a unit cube
class Cube(Object):
  def __init(self):
    Object.__init__(self)

  def contains(self, point):
    return 0 <= point.x <= 1 \
       and 0 <= point.y <= 1 \
       and 0 <= point.z <= 1


class Scene():
  def __init__(self, dimX, dimY, dimZ, resolution, obstacles):
    self.resolution = resolution
    self.bounds     = Scale(Cube(), dimX, dimY, dimZ)

    x = int(dimX / resolution)
    y = int(dimY / resolution)
    z = int(dimZ / resolution)

    self.space = np.zeros((x, y, z))

    # build the space according to the given discretisation step.
    # the space is represented as a 3D array with boolean values where True
    # means that the respective spot is occupied by an obstacle
    for i in range(x):
      for j in range(y):
        for k in range(z):
          p = Point((i + 0.5) * resolution, (j + 0.5) * resolution, (k + 0.5) * resolution)
          self.space[i, j, k] = any([obstacle.contains(p) for obstacle in obstacles])

  def getPoint(self, ix, iy, iz):
    return Point( (ix + 0.5) * self.resolution
                , (iy + 0.5) * self.resolution
                , (iz + 0.5) * self.resolution
                )

  def getCoordinate(self, point):
    return ( int(point.x  / self.resolution)
           , int(point.y  / self.resolution)
           , int(point.z  / self.resolution)
           )

  def planPath(self, start, target):
    if not self.bounds.contains(start):
      raise Exception("Start ({:.2f}, {:.2f}, {:.2f}) is out of bounds!".format(start.x, start.y, start.z))

    if not self.bounds.contains(target):
      raise Exception("Target ({:.2f}, {:.2f}, {:.2f}) is out of bounds!".format(target.x, target.y, target.z))

    startX,  startY,  startZ  = self.getCoordinate(start)
    targetX, targetY, targetZ = self.getCoordinate(target)

    if self.space[startX, startY, startZ]:
      raise Exception("Start {} point lies within an obstacle!".format(self.getPoint(startX, startY, startZ)))

    if self.space[targetX, targetY, targetZ]:
      raise Exception("Target {} point lies within an obstacle!".format(self.getPoint(targetX, targetY, targetZ)))

    explored   = set()
    unexplored = { (startX, startY, startZ) : start.distanceTo(target) }
    cameFrom   = {}
    costs      = { (startX, startY, startZ) : 0 }

    while len(unexplored) > 0:
      (currentX, currentY, currentZ), currentCost = min(unexplored.items(), key = lambda p: p[1])
      unexplored.pop((currentX, currentY, currentZ))
      explored.add((currentX, currentY, currentZ))

      if currentX == targetX and currentY == targetY and currentZ == targetZ:
        return self.reconstructPath(cameFrom, (currentX, currentY, currentZ), target)

      p = self.getPoint(currentX, currentY, currentZ)

      for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
          for dz in [-1, 0, 1]:
            x = currentX + dx
            y = currentY + dy
            z = currentZ + dz

            q = self.getPoint(x, y, z)

            if (x, y, z) not in explored and self.bounds.contains(q) and not self.space[x, y, z]:
              cost = currentCost + q.distanceTo(target)

              if (x, y, z) not in unexplored or cost < unexplored[(x, y, z)]:
                unexplored[(x, y, z)] = cost
                cameFrom[(x, y, z)]   = (currentX, currentY, currentZ)

    raise Exception("Cannot find a path to target!")

  def reconstructPath(self, cameFrom, endpoint, target):
    path = [ target
           , self.getPoint(endpoint[0], endpoint[1], endpoint[2])
           ]

    while endpoint in cameFrom:
      endpoint = cameFrom[endpoint]
      path.append(self.getPoint(endpoint[0], endpoint[1], endpoint[2]))
    return path[::-1]

if __name__ == '__main__':
  table1 = Translate(Scale(Cube(), 1.30, 0.65, 0.75), 1.35, 0.68, 0.00)
  table3 = Translate(Scale(Cube(), 1.30, 0.65, 0.75), 1.35, 1.82, 0.00)

  #table2 = Translate(Scale(Cube(), 1.30, 0.65, 0.75), 1.35, 2.68, 0.00)
  #chair  = Translate(Scale(Cube(), 0.65, 0.65, 1.00), 1.91, 1.82, 0.75)

  hugeBox = Translate(Scale(Cube(), 1.50, 1.00, 2.00), 1.3, 1.6, 0.0)

  #scene  = Scene(4.0, 4.0, 2.5, 0.15, [table1, table2, table3, chair])
  scene  = Scene(4.0, 4.0, 2.5, 0.15, [table1, table2, hugeBox])
  start  = Point(2.0, 1.0, 0.9)
  target = Point(2.0, 3.0, 0.9)

  path = scene.planPath(start, target)

  print(path)
