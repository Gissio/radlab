# Rad Lab

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Geant4](https://img.shields.io/badge/Geant4-11.x-green.svg)](https://geant4.web.cern.ch/)
[![Calzone](https://img.shields.io/badge/powered_by-Calzone-orange)](https://calzone.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**Rad Lab** is a Monte-Carlo simulation toolkit for modeling the performance of **Geiger–Müller tubes** and **scintillation detectors**. Built on top of Geant4 and Calzone, it provides an easy-to-use, reproducible, and extensible environment for detector simulation and design.

With Rad Lab, you can:

* Compute **detector efficiency** (detected particles per incident particle).
* Determine **absorbed** and **effective dose** responses (cpm per µSv/h) using [ICRP 74](https://www.icrp.org/publication.asp?id=icrp%20publication%2074) and [ICRP 116](https://www.icrp.org/publication.asp?id=icrp%20publication%20116).
* Explore the **directional response** of detectors.
* Obtain correct sensitivities for various **radiation sources**.
* Prototype and evaluate **measurement geometries**.

## Examples

Explore the included notebooks:

* [J305 Geiger tube](examples/j305/j305.ipynb)
* [M4011/J321 Geiger tube](examples/m4011-j321/m4011.ipynb)
* [HH614 Geiger tube](examples/hh614/hh614.ipynb)
* [СБМ20 (SBM20) Geiger tube](examples/sbm20/sbm20.ipynb)
* [СИЗБГ (SI3BG) Geiger tube](examples/si3bg/si3bg.ipynb)
* [LND-7317 Geiger tube](examples/si3bg/si3bg.ipynb)

## Installation

1. Install the latest **Geant4** binary release: https://geant4.web.cern.ch/download/
2. Install Python: https://www.python.org/
3. Install PIP: https://pip.pypa.io/en/stable/
4. Install Python dependencies:

   ```
   pip install -r requirements.txt
   ```

5. Install VSCode: https://code.visualstudio.com/
6. In VSCode, install the **Jupyter** extension (left toolbar → Extensions → search for "Jupyter").

## Usage

1. Start from an existing example notebook to create or modify a detector.
2. Edit the geometry file `data/geometry.toml`. (See Calzone Geometry docs: [https://calzone.readthedocs.io/en/latest/geometry.html](https://calzone.readthedocs.io/en/latest/geometry.html))
3. Open the corresponding notebook in VS Code and run the simulation.

## Coordinate system

Rad Lab uses a right-handed coordinate system:

* **x-axis:** along the detector’s length
* **y-axis:** direction of incoming radiation
* **z-axis:** upward

## Display a geometry

To display a geometry:

```
calzone display [geometry.toml]
```

For navigation instructions, see the Calzone Interactive Display docs:
[https://calzone.readthedocs.io/en/latest/display.html](https://calzone.readthedocs.io/en/latest/display.html)

## Detailed explanation

Rad Lab performs the following steps:

1. **Load geometry**

   A `geometry.toml` file specifies:

   * a `Source` box emitting parallel particles toward the detector at the coordinate origin. The source area equals the width × height of this box.
   * an `EffectiveVolume`, inside which freed electrons are counted.

2. **Run Monte-Carlo transport**

   Particle transport is simulated using Calzone/Geant4.

3. **Count ionization electrons**

   Electrons with energies above **36.4 eV** (the W-value for neon) produced in the `EffectiveVolume` are counted.
   Based on: P.A. Zyla et al., *Prog. Theor. Exp. Phys.*, Particle Data Group, 2020.

4. **Compute detector efficiency**

   Efficiency = detected electrons / incident particles.

5. **Compute dose sensitivities**

   * **Absorbed dose:** using ICRP 74 air-kerma–to-dose data.
   * **Effective dose:** using the ICRP 116 AP (anterior–posterior) geometry.

6. **Generate emission spectra**

   * **Isotopes:** spectra from `paceENSDF` (IAEA ENSDF data).
   * **X-ray tubes:** spectra from `SpekPy`.
   * **Natural background:** modeled as a simple decaying exponential.

7. **Compute equivalent effective dose** for each source.

### Supported radiation sources

| Source             | Type  | Main emissions         |
| ------------------ | ----- | ---------------------- |
| Cs-137             | γ     | 662 keV                |
| Co-60              | γ     | 1173 + 1332 keV        |
| I-131              | γ     | Complex spectrum       |
| K-40               | γ     | 1461 keV               |
| Am-241             | γ     | 59 keV                 |
| Radium             | γ     | Ra-226 chain           |
| Uranium ore        | γ     | U-235 and U-238 series |
| Uranium glaze      | γ     | Processed uranium      |
| Depleted uranium   | γ     | U-238                  |
| Thorium ore        | γ     | Th-232 series          |
| X-ray tube (60 kV) | X     | Bremsstrahlung         |
| Natural background | Mixed | Typical environmental  |

## Adding new radioactive sources

To generate or update gamma spectra, run the notebook:
[build-spectra.ipynb](tools/build-spectra.ipynb)

You will need:

* [paceENSDF](https://pypi.org/project/paceENSDF/)
* [spekPy](https://pypi.org/project/spekpy/)

## Acknowledgements

* Special thanks to **BikingBoffin** from [/r/radiation](https://www.reddit.com/r/Radiation) for inspiring this project.
