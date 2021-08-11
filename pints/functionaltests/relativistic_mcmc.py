#!/usr/bin/env python3
#
# This file is part of PINTS (https://github.com/pints-team/pints/) which is
# released under the BSD 3-clause license. See accompanying LICENSE.md for
# copyright notice and full license details.
#

from __future__ import division

import pints

from ._problems import (RunMcmcMethodOnTwoDimGaussian,
                        RunMcmcMethodOnBanana,
                        RunMcmcMethodOnHighDimensionalGaussian,
                        RunMcmcMethodOnCorrelatedGaussian,
                        RunMcmcMethodOnAnnulus,
                        RunMcmcMethodOnMultimodalGaussian,
                        RunMcmcMethodOnCone)


def two_dim_gaussian(n_iterations=None):
    if n_iterations is None:
        n_iterations = 1000
    problem = RunMcmcMethodOnTwoDimGaussian(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=200,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }


def banana(n_iterations=None):
    if n_iterations is None:
        n_iterations = 5000
    problem = RunMcmcMethodOnBanana(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=500,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }


def high_dim_gaussian(n_iterations=None):
    if n_iterations is None:
        n_iterations = 5000
    problem = RunMcmcMethodOnHighDimensionalGaussian(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=500,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }


def correlated_gaussian(n_iterations=None):
    if n_iterations is None:
        n_iterations = 5000
    problem = RunMcmcMethodOnCorrelatedGaussian(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=500,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }


def annulus(n_iterations=None):
    if n_iterations is None:
        n_iterations = 5000
    problem = RunMcmcMethodOnAnnulus(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=500,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'distance': problem.estimate_distance(),
        'mean-ess': problem.estimate_mean_ess()
    }


def multimodal_gaussian(n_iterations=None):
    if n_iterations is None:
        n_iterations = 2000
    problem = RunMcmcMethodOnMultimodalGaussian(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=500,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'kld': problem.estimate_kld(),
        'mean-ess': problem.estimate_mean_ess()
    }


def cone(n_iterations=None):
    if n_iterations is None:
        n_iterations = 2000
    problem = RunMcmcMethodOnCone(
        method=pints.RelativisticMCMC,
        n_chains=4,
        n_iterations=n_iterations,
        n_warmup=500,
        method_hyper_parameters=[20, 1, 0.1, 10]
    )

    return {
        'distance': problem.estimate_distance(),
        'mean-ess': problem.estimate_mean_ess()
    }
