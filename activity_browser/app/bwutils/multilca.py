# -*- coding: utf-8 -*-
import numpy as np
import brightway2 as bw
from bw2analyzer import ContributionAnalysis
from brightway2 import get_activity

ca = ContributionAnalysis()


class MLCA(object):
    """Wrapper class for performing LCA calculations with many functional units and LCIA methods.

    Needs to be passed a ``calculation_setup`` name.

    This class does not subclass the `LCA` class, and performs all calculations upon instantiation.

    Initialization creates `self.results`, which is a NumPy array of LCA scores, with rows of functional units and columns of LCIA methods. Ordering is the same as in the `calculation_setup`.

    Class adapted from bw2calc.multi_lca.MultiLCA to include also CONTRIBUTION ANALYSIS.

    """
    def __init__(self, cs_name):
        try:
            cs = bw.calculation_setups[cs_name]
        except KeyError:
            raise ValueError(
                "{} is not a known `calculation_setup`.".format(cs_name)
            )
        self.func_units = cs['inv']
        self.methods = cs['ia']
        self.method_dict = {}
        self.method_dict_list = []
        for i, m in enumerate(self.methods):
            self.method_dict.update({m: i})
            self.method_dict_list.append({m: i})

        self.lca = bw.LCA(demand=self.all, method=self.methods[0])
        self.lca.lci(factorize=True)
        self.method_matrices = []
        self.results = np.zeros((len(self.func_units), len(self.methods)))

        # data to be stored
        (self.rev_activity_dict, self.rev_product_dict,
         self.rev_biosphere_dict) = self.lca.reverse_dict()
        self.inventories = dict()  # Inventory (biosphere flows) for a given functional unit
        self.technosphere_flows = dict()  # Technosphere product flows for a given functional unit
        self.characterized_inventories = np.zeros(
            (len(self.func_units), len(self.methods), self.lca.biosphere_matrix.shape[0]))
        self.process_contributions = np.zeros(
            (len(self.func_units), len(self.methods), self.lca.technosphere_matrix.shape[0]))
        self.elementary_flow_contributions = np.zeros(
            (len(self.func_units), len(self.methods), self.lca.biosphere_matrix.shape[0]))

        for method in self.methods:
            self.lca.switch_method(method)
            self.method_matrices.append(self.lca.characterization_matrix)

        for row, func_unit in enumerate(self.func_units):
            self.lca.redo_lci(func_unit)

            self.inventories.update({
                str(func_unit): self.lca.biosphere_matrix
            })

            self.technosphere_flows.update({
                str(func_unit): np.multiply(self.lca.supply_array, self.lca.technosphere_matrix.diagonal())
            })

            for col, cf_matrix in enumerate(self.method_matrices):
                self.lca.characterization_matrix = cf_matrix
                self.lca.lcia_calculation()
                self.results[row, col] = self.lca.score
                #self.characterized_inventories[row, col] = self.lca.characterized_inventory
                self.process_contributions[row, col] = self.lca.characterized_inventory.sum(axis=0)
                self.elementary_flow_contributions[row, col] = np.array(
                    self.lca.characterized_inventory.sum(axis=1)).ravel()

        self.func_unit_translation_dict = {str(get_activity(list(func_unit.keys())[0])): func_unit
                                           for func_unit in self.func_units}
        self.func_key_dict = {m: i for i, m in enumerate(self.func_unit_translation_dict.keys())}
        self.func_key_list = list(self.func_key_dict.keys())

    @property
    def all(self):
        """Get all possible databases by merging all functional units"""
        return {key: 1 for func_unit in self.func_units for key in func_unit}

    @property
    def results_normalized(self):
        return self.results / self.results.max(axis=0)

    # CONTRIBUTION ANALYSIS
    def top_process_contributions_per_method(self, method_name=None, limit=5, normalised=True, limit_type="number" ):
        if method_name:
            method = self.method_dict[method_name]
        else:
            method = 0

        # Take slice for specific method from all contributions
        contribution_array = self.process_contributions[:, method, :]

        # Make normalised if required
        if normalised:
            contribution_array = self.make_nomalised(contribution_array)

        # Sort each functional unit column independently
        topcontribution_dict = {}
        for col, fu in enumerate(self.func_units):
            top_contribution = ca.sort_array(contribution_array[col, :], limit=limit, limit_type=limit_type)
            cont_per_fu = {}
            cont_per_fu.update(
                {('Rest', ''): contribution_array[col, :].sum() - top_contribution[:, 0].sum()})
            for value, index in top_contribution:
                cont_per_fu.update({self.rev_activity_dict[index]: value})
            topcontribution_dict.update({next(iter(fu.keys())): cont_per_fu})
        return topcontribution_dict

    def top_process_contributions_per_func(self, func_name=None, limit=5, normalised=True, limit_type="number"):
        if func_name:
            func = self.func_key_dict[func_name]
        else:
            func = 0

        # Take slice for specific functional unit from all contributions
        process_cont_T = self.process_contributions.T
        contribution_array = process_cont_T[:, func, :]

        # Make normalised if required
        if normalised:
            contribution_array = self.make_nomalised(contribution_array)

        # Sort each method column independently
        topcontribution_dict = {}
        for col, m in enumerate(self.method_dict_list):
            top_contribution = ca.sort_array(contribution_array[col, :], limit=limit, limit_type=limit_type)
            cont_per_m = {}
            cont_per_m.update(
                {('Rest', ''): contribution_array[col, :].sum() - top_contribution[:, 0].sum()})
            for value, index in top_contribution:
                cont_per_m.update({self.rev_activity_dict[index]: value})
            topcontribution_dict.update({next(iter(m.keys())): cont_per_m})
        return topcontribution_dict

    def top_elementary_flow_contributions_per_method(self, method_name=None, limit=5, normalised=True, limit_type="number"):
        if method_name:
            method = self.method_dict[method_name]
        else:
            method = 0

        # Take slice for specific method from all contributions
        contribution_array = self.elementary_flow_contributions[:, method, :]

        # Make normalised if required
        if normalised:
            contribution_array = self.make_nomalised(contribution_array)

        # Sort each functional unit column independently
        topcontribution_dict = {}
        for col, fu in enumerate(self.func_units):
            top_contribution = ca.sort_array(contribution_array[col, :], limit=limit, limit_type=limit_type)
            cont_per_fu = {}
            cont_per_fu.update(
                {('Rest', ''): contribution_array[col, :].sum() - top_contribution[:, 0].sum()})
            for value, index in top_contribution:
                cont_per_fu.update({self.rev_biosphere_dict[index]: value})
            topcontribution_dict.update({next(iter(fu.keys())): cont_per_fu})
        return topcontribution_dict

    def top_elementary_flow_contributions_per_func(self, func_name=None, limit=5, normalised=True, limit_type="number"):
        if func_name:
            func = self.func_key_dict[func_name]
        else:
            func = 0

        # Take slice for specific functional unit from all contributions
        process_cont_T = self.process_contributions.T
        contribution_array = process_cont_T[:, func, :]

        # Make normalised if required
        if normalised:
            contribution_array = self.make_nomalised(contribution_array)

        # Sort each method column independently
        topcontribution_dict = {}
        for col, m in enumerate(self.method_dict_list):
            top_contribution = ca.sort_array(contribution_array[col, :], limit=limit, limit_type=limit_type)
            cont_per_m = {}
            cont_per_m.update(
                {('Rest', ''): contribution_array[col, :].sum() - top_contribution[:, 0].sum()})
            for value, index in top_contribution:
                cont_per_m.update({self.rev_biosphere_dict[index]: value})
            topcontribution_dict.update({next(iter(m.keys())): cont_per_m})
        return topcontribution_dict

    def make_nomalised(self, contribution_array):
        scores = contribution_array.sum(axis=1)
        return (contribution_array / scores[:, np.newaxis])