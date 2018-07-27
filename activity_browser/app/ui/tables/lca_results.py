# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from brightway2 import get_activity, LCA, Database, methods
import random

from .dataframe_table import ABDataFrameTable


class LCAResultsTable(ABDataFrameTable):
    @ABDataFrameTable.decorated_sync
    def sync(self, lca):
        col_labels = [" | ".join(x) for x in lca.methods]
        row_labels = [str(get_activity(list(func_unit.keys())[0])) for func_unit in lca.func_units]
        self.dataframe = pd.DataFrame(lca.results, index=row_labels, columns=col_labels)

        # smooth scrolling instead of jumping from cell to cell
        self.setVerticalScrollMode(1)
        self.setHorizontalScrollMode(1)


class ProcessContributionsTable(ABDataFrameTable):
    @ABDataFrameTable.decorated_sync
    def sync(self, lca):
        col_labels = [] #
        row_labels = []
# How to deal with vastly different top 5's of processes?


class InventoryTable(ABDataFrameTable):
    @ABDataFrameTable.decorated_sync
    def sync(self, mlca, method=None):#, limit=5):
        key = random.choice(list(mlca.technosphere_flows))
        #key = method
        array = mlca.technosphere_flows[key]
        labels = [mlca.rev_activity_dict[i][1] for i in range(len(mlca.rev_activity_dict))]
        max_length = 18
        length = min(max_length, len(array))
        col_labels = ['Amount']
        row_labels = [str(i) for i in labels[:length]]
        self.dataframe = pd.DataFrame(array[:length], index=row_labels, columns=col_labels)

        # smooth scrolling instead of jumping from cell to cell
        self.setVerticalScrollMode(1)
        self.setHorizontalScrollMode(1)