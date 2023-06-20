# LaserCoolingFokkerPlanck
This repository is a part of my bachelor's thesis in Physics. The FPLitio.py file is the Python script that solves the two-dimensional Fokker-Planck equation for the atomic distribution function (a probability distribution function in space and momentum, which varies over time). This simulates a Lithium-6 atom being cooled from 1 miliKelvin to 140 microKelvin in a magneto-optical trap. The CuPy library is used to accelerate calculations using the GPU. On the other hand, the FPSodio.py file solves the same equation, but for a Sodium atom being cooled from 100 miliKelvin to 229 microKelvin.

The FPLithium6.gif and FPSodium.gif files show, as an animation, the evolution of the atomic distribution function for Lithium-6 and Sodium, respectively. The horizontal axis represents position, the vertical axis momentum, and the magnitude of the distribution function is represented as a color: where blue means it has a zero value and red represents the highest value attained by the distribution.

Any doubts and suggestions are welcome. Please send them to luieduramsol@ciencias.unam.mx
