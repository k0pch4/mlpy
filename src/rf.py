'''
Author: Apoorv Agnihotri
This implementation would be slow on larger datasets.
I would file the issues that make this implementation slow.
Coding style has been inspired from the below link,
https://github.com/random-forests/tutorials/blob/master/decision_tree.ipynb
Credits ^^^
'''

from dt import DecisionTreeClassifier, \
               DecisionTreeRegression
from multiprocessing import Pool
import utils as helper
import pandas as pd
import numpy as np
import sys

class RandomForest:
    """you don't want to instantiate this
    object directly, use a derived class.
    """
    def __init__(self,
                 method,
                 max_depth,
                 min_points,
                 num_of_trees,
                 frac,
                 jobs):
        self.method = method
        self.max_depth = max_depth
        self.min_points = min_points
        self.num_of_trees = num_of_trees
        self.frac = frac
        self.jobs = jobs
        self.trees = None
        self.roots = None

    def train(self, rows):
        """Use this function to train the RF
        """
        self.rows = rows
        # frac set to root of num_of_features / num_of_features by default
        if isinstance(self.frac, type(None)):
            p = self.rows.shape[1] # num of features
            self.frac = pow(p - 1, 0.5)/p

        # instantiate the decision tree to use
        tupl = [(self.method, self.max_depth, \
                self.min_points, self.frac)]
        tupls = tupl * self.num_of_trees

        # start jobs
        with Pool(processes=self.jobs) as pool:
            self.trees = pool.map(self._thread_train, tupls)
            self.roots = [tree.root for tree in self.trees]
        del self.rows
        return self.roots

    def _thread_train(self, tupl):
        """Internal function to be called by individual
        threads
        """
        method, max_depth, min_points, frac = tupl
        rows_without_label = self.rows.iloc[:, :-1].sample(frac=frac,
                                                           replace=False,
                                                           axis = 1)
        rows = pd.concat((rows_without_label,
                          self.rows.iloc[:, -1]),
                          axis = 1)
        dt = self.decision_tree_def(method,
                                    max_depth,
                                    min_points)
        dt.train(rows)
        return dt

    def predict(self, rows):
        """Returns the predictions as a Pd Data
        Frame. To see the individual predction
        look at <object>.preds
        """
        self.predict_rows = rows

        # start jobs and return prediction of every dt
        with Pool(processes=self.jobs) as pool:
            preds = pool.map(self._thread_predict,
                                  range(self.num_of_trees))
        """ For the case of 2 trees
        pred 1
        pred 2
        pred 3
        ---
        pred 1
        pred 2
        pred 3
        """
        # reduce to one prediction @TODO
        big = pd.DataFrame(preds[0]).transpose()

        for i in range(1, len(preds)):
            p = pd.DataFrame(preds[i]).transpose()
            big = pd.concat((big, p))
        self.preds = big.transpose() # saving for users to look at
        combined = self._prediction_function(big).transpose()
        return combined.iloc[:, :1] # return only one if more

    def _thread_predict(self, index):
        """Internal function to be called by individual
        threads
        """
        pred = self.trees[index].predict(self.predict_rows)
        return pred


class RandomForestClassifier(RandomForest):
    """Instantiate this class for a Random
    Forest Tree for classification tasks.
    """
    def __init__(self,
                 method="gini",
                 max_depth=2,
                 max_points=None,
                 num_of_trees = 4,
                 frac = 0.7,
                 jobs = 2):
        self.decision_tree_def = DecisionTreeClassifier
        super().__init__(method,
                         max_depth,
                         max_points,
                         num_of_trees,
                         frac,
                         jobs)

    def _prediction_function(self, preds):
        return pd.DataFrame(preds.mode(axis=0))


class RandomForestRegression(RandomForest):
    """Instantiate this class for a Random
    Forest for Regression tasks.
    """
    def __init__(self,
                 method="std",
                 max_depth=2,
                 max_points=None,
                 num_of_trees = 4,
                 frac = 0.7,
                 jobs = 2):
        self.decision_tree_def = DecisionTreeRegression
        super().__init__(method,
                         max_depth,
                         max_points,
                         num_of_trees,
                         frac,
                         jobs)

    def _prediction_function(self, preds):
        return pd.DataFrame(preds.mean(axis=0))
