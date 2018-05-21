crazyflie-on-voice
==================
**Important: this project is currently under construction and does not work, yet.**

*crazyflie-on-voice* allows you to voice control Crazyflie 2.0 drones.
In addition, it provides a generic HTTP control server that allows integrating the crazyflie with custom programs, as well as with a wide range of third-party systems.

Hardware requirements
---------------------
To use *crazyflie-on-voice*, you need a `Crazyflie 2.0 <https://www.bitcraze.io/crazyflie-2/>`__ and a `Loco Positioning System <https://www.bitcraze.io/loco-pos-system/>`__ (LPS).
Follow the instructions in the `LPS documentation <https://www.bitcraze.io/getting-started-with-the-loco-positioning-system/>`__ to set up your Crazyflie to work with the LPS.

Installation and setup
----------------------
*crazyflie-on-voice* requires Python 3.6 or higher.
To install *crazyflie-on-voice*, run ``pip install crazyflie-on-voice``.
Start the voice controller by running``crazyflie-on-voice "<your_crazyflie_uri>"``.
(Replace ``<your_crazyflie_uri>`` with the URI of your Crazyflie, e.g. ``radio://0/80/250K``.)


Voice control
-------------
To control your Crazyflie by voice, use the word sequence ``Crazy + <direction> + <distrance>``, where

* ``<direction>``: *up*, *down*, *left*, *right*, *ahead*, *back*, *start*, or *stop*;

* ``<distrance>``: the relative distance in centimeters, **rounded to decimeters** (e.g. *10* or *230*).

Note that the direction is absolute, considering the x,y, and z coordinates of the LPS (and not considering the yaw angle of the crazyflie).

To stop your Crazyflie, use ``Crazy stop``.

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


Pathfinding capabilities
------------------------
The drone can autonomously circumvent obstacles using a custom implementation of a an A* search-based pathfinding algorithm.
You can specify obstacles in a YAML file::

     --- # Object 1
        [0,0,0]
        [0,1,0]
        [0,0,1]
        [1,0,0]
        [0,1,1]
        [1,1,0]
        [1,0,1]
        [1,1,1]

     --- # Object 1
        [5,0,0]
        [5,1,0]
        [5,0,1]
        [6,0,0]
        [5,1,1]
        [6,1,0]
        [6,0,1]
        [6,1,1]

Then, run *crazyflie-on-voice* as follows:

``crazyflie-on-voice "<your_crazyflie_uri>" --obstacles="<path-to-yaml-file>"``

Troubleshooting voice control
-----------------------------
*crazyflie-on-voice* makes use of the *SpeechRecognition* library.
If you have problems installing the package or with voice processing, read the instructions on the `SpeechRecognition documentation page `https://pypi.org/project/SpeechRecognition/`>__ to and make sure *SpeechRecognition* works on your machine with *PocketSphinx* and *PyAudio*.

