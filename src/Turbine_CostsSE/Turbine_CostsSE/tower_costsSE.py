"""
towercost.py

Created by George Scott on 2012-08-01.
Modified by Katherine Dykes 2012.
Copyright (c) NREL. All rights reserved.
"""

from commonse.config import *
from openmdao.main.api import Component, Assembly
from openmdao.main.datatypes.api import Array, Float, Bool, Int
import numpy as np

from fusedwind.plant_cost.fused_tcc_asym import FullTowerCostModel, FullTowerCostAggregator, BaseComponentCostModel

#-------------------------------------------------------------------------------

class TowerCost(BaseComponentCostModel):

    # variables
    tower_mass = Float(iotype='in', units='kg', desc='tower mass [kg]')

    # parameters
    year = Int(iotype='in', desc='Current Year')
    month = Int(iotype='in', desc='Current Month')

    def __init__(self):
        '''
        Initial computation of the costs for the wind turbine tower component.

        Parameters
        ----------
        tower_mass : float
          mass [kg] of the wind turbine tower
        curr_yr : int
          Project start year
        curr_mon : int
          Project start month

        Returns
        -------
        cost : float
          component cost [USD]
        '''

        super(TowerCost, self).__init__()

        #controls what happens if derivatives are missing
        self.missing_deriv_policy = 'assume_zero'

    def execute(self):

        # assign input variables
        ppi.curr_yr   = self.year
        ppi.curr_mon   = self.month

        twrCostEscalator  = ppi.compute('IPPI_TWR')

        twrCostCoeff      = 1.5 # $/kg

        self.towerCost2002 = self.tower_mass * twrCostCoeff
        self.cost = self.towerCost2002 * twrCostEscalator

        # derivatives
        self.d_cost_d_tower_mass = twrCostEscalator * twrCostCoeff

    def list_deriv_vars(self):

        inputs = ['tower_mass']
        outputs = ['cost']

        return inputs, outputs

    def provideJ(self):

        # Jacobian
        self.J = np.array([[self.d_cost_d_tower_mass]])

        return self.J


#-------------------------------------------------------------------------------

class TowerCostAdder(FullTowerCostAggregator):

    def __init__(self):

        super(TowerCostAdder,self).__init__()

        #controls what happens if derivatives are missing
        self.missing_deriv_policy = 'assume_zero'

    def execute(self):

        partsCost = self.tower_cost

        # updated calculations below to account for assembly, transport, overhead and profits
        assemblyCostMultiplier = 0.0 # (4/72)
        overheadCostMultiplier = 0.0 # (24/72)
        profitMultiplier = 0.0
        transportMultiplier = 0.0

        self.cost = (1 + transportMultiplier + profitMultiplier) * ((1+overheadCostMultiplier+assemblyCostMultiplier)*partsCost)

        # derivatives
        self.d_cost_d_tower_cost = (1 + transportMultiplier + profitMultiplier) * (1+overheadCostMultiplier+assemblyCostMultiplier)

    def list_deriv_vars(self):

        inputs = ['tower_cost']
        outputs = ['cost']

        return inputs, outputs

    def provideJ(self):

        # Jacobian
        self.J = np.array([[self.d_cost_d_tower_cost]])

        return self.J


class Tower_CostsSE(FullTowerCostModel):

    # variables
    tower_mass = Float(iotype='in', units='kg', desc='tower mass [kg]')

    # parameters
    year = Int(iotype='in', desc='Current Year')
    month = Int(iotype='in', desc='Current Month')

    def __init__(self):

        super(Tower_CostsSE, self).__init__()

    def configure(self):

        super(Tower_CostsSE, self).configure()

        self.replace('towerCC', TowerCost())
        self.replace('twrcc', TowerCostAdder())

        self.connect('tower_mass', 'towerCC.tower_mass')
        self.connect('year', 'towerCC.year')
        self.connect('month', 'towerCC.month')


#-------------------------------------------------------------------------------

def example():

    # simple test of module
    tower = Tower_CostsSE()

    ppi.ref_yr   = 2002
    ppi.ref_mon  = 9

    tower.tower_mass = 434559.0
    tower.year = 2009
    tower.month =  12

    tower.run()

    print "Tower cost is ${0:.2f} USD".format(tower.cost) # $987180.30

if __name__ == "__main__":

    example()