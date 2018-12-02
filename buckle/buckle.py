# -*- coding: utf-8 -*-

"""Main module."""


import pandas as pd
import numpy as np
from scipy import constants, interpolate, optimize


def calc_area(D_o, D_i):
    return np.pi / 4 * (D_o ** 2 - D_i ** 2)


def calc_I(D_o, D_i):
    return np.pi / 64 * (D_o ** 4 - D_i ** 4)


k = np.matrix(
    [
        [80.76, 6.391e-5, 0.5, 2.407e-3, 0.06938],
        [4 * np.pi ** 2, 1.743e-4, 1, 5.532e-3, 0.1088],
        [34.06, 1.668e-4, 1.294, 1.032e-2, 0.1434],
        [28.20, 2.144e-4, 1.608, 1.047e-2, 0.1483],
    ]
)


def run_analysis(i, temp_profile):

    # --------- General Calculations -----------

    D_i = i.D_p - 2 * i.t_p
    D_c = i.D_p + 2 * i.t_c
    D_conc = D_c + 2 * i.t_conc
    D_m = D_conc + 2 * i.t_m

    A_p = calc_area(i.D_p, D_i)
    A_c = calc_area(D_c, i.D_p)
    A_conc = calc_area(D_conc, D_c)
    A_m = calc_area(D_m, D_conc)
    A_o = calc_area(D_m, 0)
    A_i = calc_area(D_i, 0)

    m_con = A_i * i.rho_con
    m_p = A_p * i.rho_p
    m_c = A_c * i.rho_c
    m_conc = A_conc * i.rho_conc
    m_m = A_m * i.rho_m
    m_w = A_o * i.rho_w

    W_s = constants.g * (m_con + m_p + m_c + m_conc + m_m - m_w)

    I_p = calc_I(i.D_p, D_i)
    I_conc = calc_I(D_conc, D_c)

    EI = i.E_p * I_p + i.Coff * i.E_conc * I_conc
    P_o = i.rho_w * constants.g * i.h

    # --------- Force Calculations -----------

    L = temp_profile["KP"].max()
    f = interpolate.interp1d(temp_profile["KP"], temp_profile["T"])
    results = pd.DataFrame(np.linspace(0, L, int(L / i.step)), columns=["x"])
    results["T"] = f(results["x"])

    results["delta_T"] = results["T"] - i.T_a
    results["F_t"] = -i.E_p * A_p * i.alpha * results["delta_T"]

    F_p = A_p * i.v * ((i.P_i * D_i - P_o * i.D_p) / (2 * i.t_p) - 0.5 * (i.P_i + P_o))
    F_e = -np.pi / 4 * (i.P_i * D_i ** 2 - P_o * i.D_p ** 2)
    results["F_eff"] = results["F_t"] + F_p + F_e + i.N_lay

    F_f_max = -i.mu_a * W_s * L / 2

    results["F_fH"] = i.mu_a * W_s * -results["x"]
    results["F_fC"] = i.mu_a * W_s * (results["x"] - L)
    results["F_f"] = results[["F_fH", "F_fC"]].max(axis=1)
    results["F_res"] = results[["F_eff", "F_f"]].max(axis=1)

    F_res_max = results["F_res"].min()

    # --------- Lateral Buckling Calculations -----------

    def buckle_force(L, mode):
        rw = mode - 1
        term1 = (k[rw, 0] * EI) / L ** 2
        term2 = k[rw, 2] * i.mu_a * W_s * L
        term3 = (
            np.sqrt(
                1
                + (
                    k[rw, 1]
                    * A_p
                    * i.E_p
                    * i.mu_l ** 2
                    * W_s
                    * L ** 5
                    / (i.mu_a * EI ** 2)
                )
            )
            - 1
        )

        return term1 + term2 * term3

    def solve_buckle_length(mode):
        x0 = np.array([100])
        return optimize.minimize(buckle_force, x0, args=mode).x[0]

    modes = np.arange(1, 5)
    buckle_lengths = np.array([solve_buckle_length(mode) for mode in modes])

    buckle_forces = np.array(
        [-buckle_force(L, mode) for L, mode in zip(buckle_lengths, modes)]
    )

    results["F_b"] = buckle_forces.max()
    results["F_actual"] = results[["F_res", "F_b"]].max(axis=1)

    return results

