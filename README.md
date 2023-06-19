# LaserCoolingFokkerPlanck
Summary: Numerical solution to a Fokker-Planck equation using the Crank-Nicholson scheme, in the context of light-matter interaction; specifically a magneto-optical.

This repository is a part of my bachelor's thesis in Physics. The FPLitio.py file is the Python script that solves the Fokker-Planck equation, which simulates a Lithium-6 atom being cooled from 1 miliKelvin to 140 microKelvin in a magneto-optical trap. The CuPy library is used to accelerate calculations using the GPU. On the other hand, the FPSodio.py file solves the same equation, but for a Sodium atom being cooled beggining from 100 miliKelvin.

The Videos folder include a GIF file and a MP4 file. These two files illustrate the evolution of the atomic distribution function along time for Lithium-6..
