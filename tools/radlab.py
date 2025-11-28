#
# Rad Lab
# Ionizing radiation detector simulation tools
#
# (C) 2025 by Gissio
#

import calzone
from concurrent.futures import ProcessPoolExecutor
import json
import math
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
from pathlib import Path
from scipy.interpolate import CubicSpline
from IPython.display import display, Markdown


# Simulations

def simulate_gm_tube(path, energy, n, pid="gamma", angle=0):
    distance = 10
    position = [distance * math.sin(angle * math.pi / 180),
                -distance * math.cos(angle * math.pi / 180),
                0]
    rotation = [0, 0, angle]
    direction = [-math.sin(angle * math.pi / 180),
                 math.cos(angle * math.pi / 180),
                 0]

    geometry = calzone.GeometryBuilder(path)                                \
        .modify("Environment.Source", position=position, rotation=rotation) \
        .build()

    simulation = calzone.Simulation(geometry=geometry)
    simulation.sample_deposits = "detailed"
    # simulation.physics.em_model = "livermore"

    source = simulation.geometry.find("Source")
    particles = simulation.particles()  \
        .pid(pid)                       \
        .energy(energy / 1000)          \
        .inside(source)                 \
        .direction(direction)           \
        .generate(n)

    result = simulation.run(particles)

    # Threshold energy for forming one electron-ion pair for neon gas.
    # Based on: P.A. Zyla et al., Prog. Theor. Exp. Phys., Particle Data Group, 2020.
    W_value = 36.4  # eV

    m = 0
    W_value_MeV = 1E-6 * W_value

    for (layer, deposits) in result.deposits.items():
        last_event = None
        for deposit in deposits.line:
            event = deposit["event"]
            value = deposit["value"]

            if value >= W_value_MeV and event != last_event:
                last_event = event
                m += 1

    return (energy, angle, m)


def get_source_area(path):
    # Check geometry

    simulation = calzone.Simulation(path)
    simulation.geometry.check()

    # Source area

    source = simulation.geometry.find("Source")
    aabb = source.aabb()

    return aabb[1][0] - aabb[0][0] * (aabb[1][2] - aabb[0][2])


def simulate_gm_energies(path, n_montecarlo, pid="gamma"):
    energies_num = 32
    chunk_size = 100000

    chunk_num = math.ceil(n_montecarlo / chunk_size)
    workers_num = int((multiprocessing.cpu_count() + 1) / 2)
    energies = np.logspace(np.log10(10), np.log10(3600),
                           energies_num).tolist()
    efficiencies = [0] * energies_num
    multiprocessing.freeze_support()

    with ProcessPoolExecutor(max_workers=workers_num) as executor:
        futures = []
        for energy in energies:
            for i in range(chunk_num):
                futures.append(executor.submit(simulate_gm_tube,
                               path, energy, chunk_size))

        for future in futures:
            energy, angle, m = future.result()
            index = energies.index(energy)
            efficiencies[index] += m / (chunk_num * chunk_size)

    return energies, efficiencies


def simulate_gm_angles(path, n_montecarlo):
    energy = 661.7
    angles_num = int((180 / 10) + 1)
    chunk_size = 100000

    chunk_num = math.ceil(n_montecarlo / chunk_size)
    workers_num = int((multiprocessing.cpu_count() + 1) / 2)
    angles = np.linspace(-90, 90, angles_num).tolist()
    efficiencies = [0] * angles_num
    multiprocessing.freeze_support()

    with ProcessPoolExecutor(max_workers=workers_num) as executor:
        futures = []
        for angle in angles:
            for i in range(chunk_num):
                futures.append(executor.submit(simulate_gm_tube,
                               path, energy, chunk_size, angle=angle))

        for future in futures:
            energy, angle, m = future.result()
            index = angles.index(angle)
            efficiencies[index] += m / (chunk_num * chunk_size)

    return angles, efficiencies


# Calculations

def calculate_ambient_dose_equivalent_sensitivities(energies, efficiencies, source_area):
    # Load ambient dose equivalent per fluence data

    path = Path(__file__).parent / "data" / "icrp74_photons_H10.txt"
    H10_data = np.loadtxt(path, skiprows=3, encoding='utf-8').transpose()
    H10_energies = H10_data[0]
    H_t = H10_data[1]
    H_t_cs = CubicSpline(np.log10(H10_energies), H_t, bc_type='natural')

    # Calculate ambient dose equivalent sensitivities

    sensitivities = []
    for index, energy in enumerate(energies):
        efficiency = efficiencies[index]
        H_t_value = H_t_cs(np.log10(1E-3 * energy)).tolist()
        sensitivity = (60 / 3600 / 1E-6) * source_area * \
            efficiency / H_t_value
        sensitivities.append(sensitivity)

    return sensitivities


def calculate_source_sensitivities(energies, dose_sensitivities):
    # Load source spectra

    path = Path(__file__).parent / "data" / "spectra.json"
    with open(path, "r") as f:
        spectra = json.load(f)

    # Model dose sensitivities

    cs = CubicSpline(np.log10(energies), dose_sensitivities, bc_type='natural')

    # Calculate source sensitivities

    source_sensitivities = {}

    for nuclide in spectra:
        spectrum = spectra[nuclide]

        numerator_sum = 0
        denominator_sum = 0

        for energy in spectrum:
            energy_value = float(energy)

            # Evaluate only energies in simulated range
            if energy_value >= energies[0] or energy_value <= energies[-1]:
                intensity = spectrum[energy]

                cs_value = cs(np.log10(energy_value)).tolist()
                if cs_value > 1E-3:
                    numerator_sum += intensity
                    denominator_sum += intensity / cs_value

        source_sensitivities[nuclide] = numerator_sum / denominator_sum

    return source_sensitivities


# Plots

def plot_semilogx(title_label, x, y, data_label, normalize_cs137=False):
    cs = CubicSpline(np.log10(x), y, bc_type='natural')

    cs_x = np.logspace(np.log10(x[0]), np.log10(x[-1]), 500)
    cs_y = cs(np.log10(cs_x))

    if normalize_cs137:
        cs_y /= cs(np.log10(661.657))

    plt.figure()
    plt.semilogx(cs_x, cs_y)
    plt.xlabel("Energy E (keV)")
    plt.ylabel(data_label)
    plt.title(f"{title_label}")
    plt.grid(True)
    plt.show()


def plot_polar(title_label, x, y):
    x = np.array(x) * np.pi / 180
    cs = CubicSpline(x, y, bc_type='natural')

    cs_x = np.linspace(x[0], x[-1], 500)
    cs_y = cs(cs_x)
    cs_y_norm = cs(0)
    if cs_y_norm > 0:
        cs_y /= cs_y_norm

    plt.figure()
    plt.polar(cs_x, cs_y)
    ax = plt.gca()
    ax.set_thetamin(-90)
    ax.set_thetamax(90)
    ax.set_theta_offset(np.pi / 2)
    plt.title(f"{title_label}")
    plt.grid(True)
    plt.show()


# Tables

def print_source_sensitivities(source_sensitivities):
    cs137_sensitivity = source_sensitivities["Cs-137"]

    md = "| Source | Sensitivity (cpm/µSv/h) | Relative sensitivity (Cs-137) |\n|-|-|-|\n"
    for key, value in source_sensitivities.items():
        rel_value = value / cs137_sensitivity
        md += f"| {key} | {value:.3f} | {rel_value:.3f} |\n"

    display(Markdown(md))
