# -*- coding: utf-8 -*-

"""Lateral buckling module."""

from collections import OrderedDict

import pandas as pd
import numpy as np
from scipy import constants, interpolate, optimize

from pipe import logger


def calc_d(D_o, t, inner=False):
    """Return the outer or inner diameter [m].
    
    :param float D_o: Outer diameter [m]
    :param float t: Layer thickness [m]
    :param boolean inner: Select diameter    
    """
    if inner:
        return D_o - 2 * t
    else:
        return D_o + 2 * t


def calc_area(D_o, D_i):
    """Return the cross-sectional area [m²]."""
    return np.pi / 4 * (D_o ** 2 - D_i ** 2)


def calc_W_s(layers, A_o, rho_w):
    """Return the submerged weight [kg/m³]."""
    m = 0
    for A, i in layers:
        m += A * i
    return constants.g * (m - A_o * rho_w)


def calc_I(D_o, D_i):
    """Return the second moment of area [m^4]."""
    return np.pi / 64 * (D_o ** 4 - D_i ** 4)


def calc_P_i(P_d, rho_c, h, h_ref):
    """Return the local internal pressure [Pa]."""
    return P_d + rho_c * constants.g * (h + h_ref)


def calc_eaf(delta_T, N_lay, P_i, A_i, v, A_p, D_i, t_p, alpha, E_p, thick=False):
    """Return the effective axial force [N], negative in compression."""
    if thick:
        return (
            N_lay
            - P_i * A_i
            + 2 * P_i * v * (A_p / 4) * (D_i / t_p - 1)
            - alpha * delta_T * E_p * A_p
        )
    else:
        return N_lay - P_i * A_i * (1 - 2 * v) - A_p * E_p * alpha * delta_T


def calc_buckle_forces(EI, W_s, A_p, E_p, mu_l, mu_a):
    """Return an array of buckle forces [N] for modes 1-4 and infinte, negative in
    compression."""

    def buckle_force(L, mode):

        k = np.matrix(
            [
                [80.76, 6.391e-5, 0.5, 2.407e-3, 0.06938],
                [4 * np.pi ** 2, 1.743e-4, 1, 5.532e-3, 0.1088],
                [34.06, 1.668e-4, 1.294, 1.032e-2, 0.1434],
                [28.20, 2.144e-4, 1.608, 1.047e-2, 0.1483],
            ]
        )

        rw = mode - 1
        term1 = (k[rw, 0] * EI) / L ** 2
        term2 = k[rw, 2] * mu_a * W_s * L
        term3 = (
            np.sqrt(
                1 + (k[rw, 1] * A_p * E_p * mu_l ** 2 * W_s * L ** 5 / (mu_a * EI ** 2))
            )
            - 1
        )

        return term1 + term2 * term3

    def solve_buckle_length(mode):
        return optimize.minimize(buckle_force, x0=100, args=mode).x[0]

    modes = np.arange(1, 5)
    buckle_lengths = np.array([solve_buckle_length(mode) for mode in modes])

    return np.array([-buckle_force(L, mode) for L, mode in zip(buckle_lengths, modes)])


def run_analysis(i, temp, depth):

    # --------- General Calculations -----------

    D_i = calc_d(i.D_p, i.t_p, inner=True)
    D_c = calc_d(i.D_p, i.t_c)
    D_conc = calc_d(D_c, i.t_conc)
    D_m = calc_d(D_conc, i.t_m)

    A_p = calc_area(i.D_p, D_i)
    A_c = calc_area(D_c, i.D_p)
    A_conc = calc_area(D_conc, D_c)
    A_m = calc_area(D_m, D_conc)
    A_o = calc_area(D_m, 0)
    A_i = calc_area(D_i, 0)

    W_s = calc_W_s(
        (
            (A_i, i.rho_con),
            (A_p, i.rho_p),
            (A_c, i.rho_c),
            (A_conc, i.rho_conc),
            (A_m, i.rho_m),
        ),
        A_o,
        i.rho_w,
    )

    I_p = calc_I(i.D_p, D_i)
    I_conc = calc_I(D_conc, D_c)

    EI = i.E_p * I_p + i.Coff * i.E_conc * I_conc

    P_i = calc_P_i(i.P_d, i.rho_c, i.h, i.h_ref)

    # --------- Force Calculations -----------

    L = temp["KP"].max()
    results = pd.DataFrame(np.linspace(0, L, int(L / i.step) + 1), columns=["x"])

    f = interpolate.interp1d(temp["KP"], temp["T [°C]"])
    results["T"] = f(results["x"])

    results["delta_T"] = results["T"] - i.T_a

    results["F_eff"] = np.vectorize(calc_eaf)(
        results["delta_T"],
        i.N_lay,
        P_i,
        A_i,
        i.v,
        A_p,
        D_i,
        i.t_p,
        i.alpha,
        i.E_p,
        i.thick,
    )

    results["F_fH"] = i.mu_a * W_s * -results["x"]
    results["F_fC"] = i.mu_a * W_s * (results["x"] - L)
    results["F_f"] = results[["F_fH", "F_fC"]].max(axis=1)
    results["F_res"] = results[["F_eff", "F_f"]].max(axis=1)

    # --------- Lateral Buckling Calculations -----------

    results["F_b"] = calc_buckle_forces(EI, W_s, A_p, i.E_p, i.mu_l, i.mu_a).max()
    results["F_actual"] = results[["F_res", "F_b"]].max(axis=1)

    # --------- Log intermediate results for debugging -----------

    logger.debug(f"Submerged Weight [N]: {W_s}")
    logger.debug(f"Bending Stiffness [N/m]: {EI}")
    logger.debug(f"Local Internal Pressure [Pa]: {P_i}")

    return results
