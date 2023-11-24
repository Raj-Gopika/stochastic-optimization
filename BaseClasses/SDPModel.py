from collections import namedtuple
import numpy as np
from abc import ABC, abstractmethod


class SDPModel(ABC):
    """
    Sequential decision problem base class

    This class represents a base class for sequential decision problems.
    It provides methods for initializing the problem, resetting the state,
    performing a single step in the problem, and updating the time index.

    Attributes:
        State (namedtuple): Named tuple representing the state variables.
        Decision (namedtuple): Named tuple representing the decision variables.
        state_names (list): List of state variable names.
        decision_names (list): List of decision variable names.
        initial_state (State): Initial state of the problem.
        state (State): Current state of the problem.
        objective (float): Objective value of the problem.
        t (float): Current time index.
        T (float): Terminal time.
        prng (RandomState): Random number generator.

    Methods:
        __init__: Initializes an instance of the SDPModel class.
        reset: Resets the SDPModel to its initial state.
        build_state: Sets the new state values using the provided information.
        build_decision: Builds a decision object using the provided information.
        exog_info_fn: Abstract method for generating exogenous information.
        transition_fn: Abstract method for computing the state transition.
        objective_fn: Abstract method for computing the objective value.
        update_t: Updates the value of the time index.
        step: Performs a single step in the sequential decision problem.
    """

    def __init__(
        self,
        state_names: list,
        decision_names: list,
        S0: dict,
        t0: float = 0,
        T: float = 1,
        seed: int = 42,
    ) -> None:
        """
        Initializes an instance of the SDPModel class.

        Args:
            state_names (list): List of state variable names.
            decision_names (list): List of decision variable names.
            S0 (dict): Initial state values.
            t0 (float, optional): Initial time. Defaults to 0.
            T (float, optional): Terminal time. Defaults to 1.
            seed (int, optional): Seed for random number generation. Defaults to 42.
        """
        self.State = namedtuple("State", state_names)
        self.Decision = namedtuple("Decision", decision_names)

        self.state_names = state_names
        self.decision_names = decision_names

        self.initial_state = self.build_state(S0)
        self.state = self.build_state(S0)

        self.objective = 0.0
        self.t = t0
        self.T = T
        self.prng = np.random.RandomState(seed)

    def reset(self):
        """
        Resets the SDPModel to its initial state.

        This method resets the state, objective, and time variables of the SDPModel
        to their initial values.

        Parameters:
            None

        Returns:
            None
        """
        self.state = self.build_state(self.initial_state)
        self.objective = 0.0
        self.t = 0.0
        pass

    def build_state(self, info: dict):
        """
        Sets the new state values using the provided information.

        Args:
            info (dict): A dictionary containing the new values for all state variables.

        Returns:
            State: The updated state object.
        """
        return self.State(*[info[k] for k in self.state_names])

    def build_decision(self, info: dict):
        """
        Builds a decision object using the provided information.

        Args:
            info (dict): A dictionary containing the new values for all decision variables.

        Returns:
            Decision: The decision object.
        """
        return self.Decision(*[info[k] for k in self.decision_names])

    @abstractmethod
    def exog_info_fn(self, decision):
        """
        Abstract method for generating exogenous information.

        This method should be implemented in the derived classes to generate
        the exogenous information based on the current decision.

        Args:
            decision: The current decision.

        Returns:
            dict: A dictionary containing the exogenous information.
        """
        pass

    @abstractmethod
    def transition_fn(self, decision, exog_info):
        """
        Abstract method for computing the state transition.

        This method should be implemented in the derived classes to compute
        the state transition based on the current state, decision, and exogenous information.

        Args:
            decision: The current decision.
            exog_info (dict): The exogenous information.

        Returns:
            dict: A dictionary containing the updated state variables.
        """
        pass

    @abstractmethod
    def objective_fn(self, decision, exog_info):
        """
        Abstract method for computing the objective value.

        This method should be implemented in the derived classes to compute
        the objective value contribution based on the current state, decision,
        and exogenous information.

        Args:
            decision: The current decision.
            exog_info (dict): The exogenous information.

        Returns:
            float: The objective value.
        """
        pass

    def update_t(self):
        """
        Update the value of the time index t.
        """
        self.t += 1

    def step(self, decision):
        """
        Performs a single step in the sequential decision problem.

        Args:
            decision: The decision made at the current state.

        Returns:
            The new state after the step.
        """
        # Generate new exogenous information
        exog_info = self.exog_info_fn(decision)

        # Compute objective based on W_t+1, x_t, S_t (state is not updated yet)
        self.objective += self.objective_fn(decision, exog_info)

        # Execute transition function and add new state to exog_info dict
        exog_info.update(self.transition_fn(decision, exog_info))

        # Build new state from state variables and (optionally) exog_info variables.
        # This is helpful if some of the exogenous variables are also state variables.
        self.state = self.build_state(exog_info)

        # Update time counter
        self.update_t()

        # From the returned state S_t+1, the policy generates a new decision
        return self.state
