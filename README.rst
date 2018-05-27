crazyflie-on-voice
==================
.. image:: https://travis-ci.org/TimKam/crazyflie-on-voice.svg?branch=master
    :target: https://travis-ci.org/TimKam/crazyflie-on-voice
    
**Important: this project is currently under construction and does not work, yet.**

*crazyflie-on-voice* provides a generic HTTP control server that allows integrating the crazyflie with custom programs, as well as with a wide range of third-party systems.
In addition, *crazyflie-on-voice* provides a client that allows you to voice control Crazyflie 2.0 drones.

Hardware requirements
---------------------
To use *crazyflie-on-voice*, you need a `Crazyflie 2.0 <https://www.bitcraze.io/crazyflie-2/>`__ and a `Loco Positioning System <https://www.bitcraze.io/loco-pos-system/>`__ (LPS).
Follow the instructions in the `LPS documentation <https://www.bitcraze.io/getting-started-with-the-loco-positioning-system/>`__ to set up your Crazyflie to work with the LPS.

Installation and setup
----------------------
*crazyflie-on-voice* requires Python 3.6 or higher.
To get started, proceed as follows:

* To install *crazyflie-on-voice*, run ``pip install crazyflie-on-voice``.

* To start the crazyflie controller, run ``crazyflie-on-voice --uri=<your_crazyflie_uri>``.
  (Replace ``<your_crazyflie_uri>`` with the URI of your Crazyflie, e.g. ``radio://0/80/250K``.)

* Start the voice control client by running ``crazyflie-on-voice --voice-only``.

Options
-------
The following command line options are available:

* ``--uri``, ``-u``: URI of the crazyflie. Defaults to ``radio://0/110/2M``

* ``--control-port``, ``-cp``: Port for the control server. Defaults to ``8000``.

* ``--planing-port``, ``-pp``: Port for the planning server. Defaults to ``8001``.

* ``--room-spec``, ``-rs``: Path to the room specification file. (see *Path planning* below). Defaults to ``./examples/room_spec_1.yaml``.

* ``--voice`, ``-v``: Add, if you *also* want to start the voice control client. (The voice control client does not start by default.)

* ``--voice-only`, ``-vo``:  Add, if you *only* want to start the voice control client.

* ``--voice-api``, ``-va``: Speech-to-text API the voice control client users. Either ``google`` (software-as-a-service) or ``pocketsphinx`` (free software, local installation). Defaults to ``google``.

Voice control
-------------
To control your Crazyflie by voice, use the word sequence ``Crazy + <direction> + <distrance>``, where

* ``<direction>``: *up*, *down*, *left*, *right*, *ahead*, *back*, *start*, or *stop*;

* ``<distrance>``: the relative distance in centimeters, **rounded to decimeters** (e.g. *10* or *230*).

Note that the direction is absolute, considering the x,y, and z coordinates of the LPS (and not considering the yaw angle of the crazyflie).

To stop your Crazyflie, use ``Crazy stop``.

Pathfinding capabilities
------------------------
The Crazyflie can autonomously circumvent obstacles using a custom implementation of a an `A* search<https://en.wikipedia.org/wiki/A*_search_algorithm>`__-based pathfinding algorithm.
The bounds of the environment as well as the obstacles within the environment must be described and are assumed to be static.
Currently, obstacles are described as unit cubes which are then scaled and translated so they represent objects of the correct size and position in the environment.
(Rotation of objects is currently not possible but could be added easily.)
For path planning, the scene is discretised as a cartesian grid with cell size 0.1m x 0.1m x 0.1m.
There is no benefit in using smaller cells since the accuracy of the positioning system is limited.
For each grid cell, all obstacles are sampled to determine whether they are occupied.
The grid is then used to find the shortest path that avoids obstacles between two points using A*.

You can model your environment as a `YAML <https://en.wikipedia.org/wiki/YAML>`__ file.
For example, an obstacle of size 1.6m x 0.8m x 2.2m that has its "origin" at position 1.25m x 1.7m on the floor can be modelled like this::

    - obstacle:
        - [1.60, 0.8, 2.20]
        - [1.25, 1.70, 0.00]


You should also provide the measures of the room in which you are flying (as the first entry in your YAML file).
Here is an example of a full specification::

    - room:
      - [4.0, 5.0, 2.5]

    - table1:
      - [1.30, 0.65, 0.75]
      - [1.35, 0.68, 0.00]

    - table2:
      - [1.30, 0.65, 0.75]
      - [1.35, 2.68, 0.00]

    - obstacle:
      - [1.60, 0.8, 2.20]
      - [1.25, 1.70, 0.00]

The first item **has to be** the room measures specification.
Note that for each obstacle, the first array specifies the measures ``[x, y, z]`` in meters;
the second array specifies the coordinates of the corner that is closest to ``[0, 0, 0]``.

Then, run *crazyflie-on-voice* as follows:

``crazyflie-on-voice "<your_crazyflie_uri>" --room-spec="<path-to-yaml-file>"``

Generic HTTP interface
----------------------
*crazyflie on voice* consists of two main components: a voice control client and a generic HTTP server.
To only run the HTTP server, exectue ``crazyflie-on-voice --server --port=<port>``.
Replace ``<port>`` with the port on which you want your server to run.

The server accepts ``POST`` requests to its base URL. The requests have to have the following structure:

* either::

    {"command": "<command>"},

   , where command is either ``stop`` or ``start``.

* or::

    {"distance": ["<x>, <y>, <z>]}

  , where ``<x>``, ``<y>``, ``<z>`` is the **change** in x, y, and z coordinates you want to achieve.

  For example::

    {"distance": [0, 0, 0.5]}}


Troubleshooting voice control
-----------------------------
*crazyflie-on-voice* makes use of the *SpeechRecognition* library.
In case you want to use *crazyflie-on-voice* with *PocketSphinx* and you have problems installing the package or with voice processing, read the instructions on the `SpeechRecognition documentation page <https://pypi.org/project/SpeechRecognition/>`__ to and make sure *SpeechRecognition* works on your machine with *PocketSphinx* and *PyAudio*.

