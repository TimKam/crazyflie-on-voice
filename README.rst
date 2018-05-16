crazyflie-on-voice
==================
**Important: this project is currently under construction and does not work, yet.**

*crazyflie-on-voice* allows you to voice control Crazyflie 2.0 drones.

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


Control
-------
To control your Crazyflie, use the word sequence ``Crazy + <direction> + <distrance>``, where

* ``<direction>``: *go up*, *lower*, *left*, *right*, *ahead*, *back*, or *start landing*;

* ``<distrance>``: the relative distance in centimeters, **rounded to decimeters** (e.g. *10* or *230*).

Note that the direction is absolute, considering the x,y, and z coordinates of the LPS (and not considering the yaw angle of the crazyflie).

To stop your Crazyflie, use ``Crazy stop``.

Troubleshooting voice control
-----------------------------
*crazyflie-on-voice* makes use of the *SpeechRecognition* library.
If you have problems installing the package or with voice processing, read the instructions on the `SpeechRecognition documentation page `https://pypi.org/project/SpeechRecognition/`>__ to and make sure *SpeechRecognition* works on your machine with *PocketSphinx* and *PyAudio*.

