#
# Sub-module containing sequential MC inference routines
#
# This file is part of PINTS.
#  Copyright (c) 2017, University of Oxford.
#  For licensing information, see the LICENSE file distributed with the PINTS
#  software package.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import pints
import numpy as np
from scipy.special import logsumexp


class SMCSampler(object):
    """
    Abstract base class for sequential Monte Carlo samplers.

    Arguments:

    ``log_posterior``
        A :class:`LogPosterior` function that evaluates points in the parameter
        space.

    """
    def __init__(self, log_posterior, x0, sigma0=None):

        # Store log_likelihood and log_prior
        if not isinstance(log_posterior, pints.LogPDF):
            raise ValueError(
                'Given posterior function must extend pints.LogPDF')
        self._log_posterior = log_posterior

        # Check initial position
        self._x0 = pints.vector(x0)

        # Get dimension
        self._dimension = len(self._x0)

        # Check initial standard deviation
        if sigma0 is None:
            # Get representative parameter value for each parameter
            self._sigma0 = np.abs(self._x0)
            self._sigma0[self._sigma0 == 0] = 1
            # Use to create diagonal matrix
            self._sigma0 = np.diag(0.01 * self._sigma0)
        else:
            self._sigma0 = np.array(sigma0)
            if np.product(self._sigma0.shape) == self._dimension:
                # Convert from 1d array
                self._sigma0 = self._sigma0.reshape((self._dimension,))
                self._sigma0 = np.diag(self._sigma0)
            else:
                # Check if 2d matrix of correct size
                self._sigma0 = self._sigma0.reshape(
                    (self._dimension, self._dimension))

        # Get dimension
        self._dimension = self._log_posterior.n_parameters()

        if not isinstance(log_posterior, pints.LogPosterior):
            lower = np.repeat(-100, self._dimension)
            upper = np.repeat(+100, self._dimension)
            self._log_prior = pints.UniformLogPrior(lower, upper)
        else:
            self._log_prior = self._log_posterior._log_prior

        # Logging
        self._log_to_screen = True
        self._log_filename = None
        self._log_csv = False
        self.set_log_rate()

        # Parallelisation
        self._parallel = False
        self._n_workers = 1
        self.set_parallel()

        # Initial starting parameters
        self._mu = self._x0
        self._sigma = self._sigma0
        self._method = pints.AdaptiveCovarianceMCMC
        self._chain = self._method(self._x0, self._sigma0)

        # Initial phase (needed for e.g. adaptive covariance)
        self._initial_phase_iterations = 0
        # self._needs_initial_phase = self._method.needs_initial_phase()
        # if self._needs_initial_phase:
        #     self.set_initial_phase_iterations()

        # Temperature schedule
        self._schedule = None
        self.set_temperature_schedule()

        # Set run params
        self._particles = 1000
        self._initialise()

        # ESS threshold (default from Del Moral et al.)
        self._ess_threshold = self._particles / 2

        # Determines whether to resample particles at end of
        # steps 2 and 3 from Del Moral et al. (2006)
        self._resample_end_2_3 = True

        # Set number of MCMC steps to do for each distribution
        self._kernel_samples = 1

    def _initialise(self):
        """
        Initialises SMC
        """
        self._samples = np.random.multivariate_normal(
            mean=self._mu, cov=self._sigma, size=self._particles)
        self._samples_log_pdf = np.zeros(self._particles)
        self._weights = np.zeros(self._particles)
        for i in range(self._particles):
            self._samples_log_pdf[i] = self._log_posterior(self._samples[i])
            log_prior_pdf = self._log_prior(self._samples[i])
            self._weights[i] = (
                self._schedule[1] * self._samples_log_pdf[i] +
                (1 - self._schedule[1]) * log_prior_pdf -
                log_prior_pdf
            )

    def set_particles(self, particles):
        """
        Sets the number of particles
        """
        if particles < 10:
            raise ValueError('Must have more than 10 particles in SMC.')
        self._initialise()

    def set_resample_end_2_3(self, resample_end_2_3):
        """
        Determines whether a resampling step is performed at end of
        steps 2 and 3 in Del Moral et al. Algorithm 3.1.1
        """
        if not isinstance(resample_end_2_3, bool):
            raise ValueError('Resample_end_2_3 should be boolean.')
        self._resample_end_2_3 = resample_end_2_3

    def set_ess_threshold(self, ess_threshold):
        """
        Sets the threshold ESS (effective sample size)
        """
        if ess_threshold > self._particles:
            raise ValueError('ESS threshold must be below actual sample size.')
        if ess_threshold < 0:
            raise ValueError('ESS must be greater than zero.')
        self._ess_threshold = ess_threshold

    def set_kernel_samples(self, kernel_samples):
        """
        Sets number of MCMC samples to do for each temperature
        """
        if kernel_samples < 1:
            raise ValueError('Number of samples per temperature must be >= 1.')
        if not isinstance(kernel_samples, int):
            raise ValueError('Number of samples per temperature must be int.')
        self._kernel_samples = kernel_samples

    def set_temperature_schedule(self, schedule=10):
        """
        Sets a temperature schedule.

        If ``schedule`` is an ``int`` it is interpreted as the number of
        temperatures and a schedule is generated that is uniformly spaced on
        the log scale.

        If ``schedule`` is a list (or array) it is interpreted as a custom
        temperature schedule.
        """

        # Check type of schedule argument
        if np.isscalar(schedule):

            # Set using int
            schedule = int(schedule)
            if schedule < 2:
                raise ValueError(
                    'A schedule must contain at least two temperatures.')

            # Set a temperature schedule that is uniform on log(T)
            a_max = 0
            a_min = np.log(0.0001)
            #diff = (a_max - a_min) / schedule
            log_schedule = np.linspace(a_min, a_max, schedule)
            self._schedule = np.exp(log_schedule)
            self._schedule.setflags(write=False)

        else:

            # Set to custom schedule
            schedule = pints.vector(schedule)
            if len(schedule) < 2:
                raise ValueError(
                    'A schedule must contain at least two temperatures.')
            if schedule[0] != 0:
                raise ValueError(
                    'First element of temperature schedule must be 0.')

            # Check vector elements all between 0 and 1 (inclusive)
            if np.any(schedule < 0):
                raise ValueError('Temperatures must be non-negative.')
            if np.any(schedule > 1):
                raise ValueError('Temperatures cannot exceed 1.')

            # Store
            self._schedule = schedule

    def ask(self):
        """
        Returns a position in the search space to evaluate.
        """
        self._proposed = self._chain.ask()
        return self._proposed

    def tell(self, fx):
        """
        Performs an iteration of the MCMC algorithm, using the evaluation
        ``fx`` of the point previously specified by ``ask``. Returns the next
        sample in the chain.
        """
        raise NotImplementedError

    def run(self):
        """
        Runs the SMC sampling routine.
        """

        # Create evaluator object
        if self._parallel:
            # Use at most n_workers workers
            n_workers = min(self._n_workers, self._chains)
            evaluator = pints.ParallelEvaluator(
                self._log_likelihood, n_workers=n_workers)
        else:
            evaluator = pints.SequentialEvaluator(self._log_likelihood)

        # Set up progress reporting
        next_message = 0
        message_warm_up = 3
        message_interval = 20

        # Start logging
        logging = self._log_to_screen or self._log_filename
        if logging:
            # Create timer
            timer = pints.Timer()

            if self._log_to_screen:
                # Show current settings
                print('Running ' + self.name())
                print('Total number of particles: ' + str(self._particles))
                print('Number of temperatures: ' + str(len(self._schedule)))
                if self._resample_end_2_3:
                    print('Resampling at end of each iteration')
                else:
                    print('Not resampling at end of each iteration')
                print(
                    'Number of MCMC steps at each temperature: '
                    + str(self._kernel_samples))

            # Set up logger
            logger = pints.Logger()
            if not self._log_to_screen:
                logger.set_stream(None)
            if self._log_filename:
                logger.set_filename(self._log_filename, csv=self._log_csv)

            # Add fields to log
            logger.add_counter('Iter.', max_value=self._iterations)
            logger.add_counter('Eval.', max_value=self._iterations * 10)
            #TODO: Add other informative fields ?
            logger.add_time('Time m:s')

        # Run!
        for i in range(0, self._iterations):
            # Set current temperature
            self._current_temperature = self._schedule[i + 1]

            for j in range(self._particles):
                self._current = self._samples[j]
                # Use some method to propose new samples
                self._proposed = self.ask()

                # Evaluate their fit
                fx = evaluator.evaluate([self._proposed])[0]

                # prior evaluation
                log_prior_pdf = self._log_prior(self._proposed)

                # Use tell from adaptive covariance MCMC
                self._current_log_pdf = self._samples_log_pdf[j]
                self._samples[j] = self.tell(
                    self._current_temperature * fx +
                    (1 - self._current_temperature) * log_prior_pdf
                )

                # translate _current_log_pdf back into posterior pdf value
                self._samples_log_pdf[j] = (
                    (1.0 / self._current_temperature) *
                    (self._current_log_pdf -
                     (1 - self._current_temperature) * log_prior_pdf)
                )

            # Show progress
            if logging:
                i_message += 1
                if i_message >= next_message:
                    # Log state
                    logger.log(i_message, self._n_evals, timer.time())

                    # Choose next logging point
                    if i_message > message_warm_up:
                        next_message = message_interval * (
                            1 + i_message // message_interval)

        # Calculate log_evidence and uncertainty
        self._log_Z = self.marginal_log_likelihood()
        self._log_Z_sd = self.marginal_log_likelihood_standard_deviation()

        # Draw samples from posterior
        n = self._posterior_samples
        self._m_posterior_samples = self.sample_from_posterior(n)

        return self._m_posterior_samples

    def _tempered_distribution(self, x, beta):
        """
        Returns the tempered log-pdf:
        ``beta * log pi(x) + (1 - beta) * log prior(x)``
        If not explicitly given prior is assumed to be multivariate normal.
        """
        return beta * self._log_posterior(x) + (1 - beta) * self._log_prior(x)

    def _w_tilde(self, x_old, x_new, beta_old, beta_new):
        """
        Calculates the log unnormalised incremental weight as per eq. (31) in
        Del Moral.
        """
        return (
            self._tempered_distribution(x_old, beta_new)
            - self._tempered_distribution(x_old, beta_old)
        )

    def _new_weight(self, w_old, x_old, x_new, beta_old, beta_new):
        """
        Calculates the log new weights as per algorithm 3.1.1. in Del Moral et
        al. (2006).
        """
        w_tilde_value = self._w_tilde(x_old, x_new, beta_old, beta_new)
        return np.log(w_old) + w_tilde_value

    def _new_weights(
            self, w_old, samples_old, samples_new, beta_old, beta_new):
        """
        Calculates the new weights as per algorithm 3.1.1 in Del Moral et al.
        (2006).
        """
        w_new = np.array([
            self._new_weight(
                w, samples_old[i], samples_new[i], beta_old, beta_new)
            for i, w in enumerate(w_old)])

        return np.exp(w_new - logsumexp(w_new))