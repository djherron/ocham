#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: David Herron
"""

'''
This script drives testing of the OCHAM tool.  If also serves as an
OCHAM tool usage example.
'''

#%% imports

from ocham_tool import OCHAM

import ocham_tool_utils as ochamu


#%% instantiate an OCHAM tool object

# At instantiation, the OCHAM tool consumes an OWL ontology and represents
# its class hierarchy as an adjacency matrix.  Nothing is returned to the
# user at instantiation.

#
# configure the parameters for the OCHAM tool
#

# set ontology filename
ontology_filename = 'onto-01.ttl'

# set the method to be used for computing the transitive closure of the
# class hierarchy asserted in the OWL ontology; they all produce the same
# results
#
# valid values:
# 0 - do not compute the transitive closure of the class hierarchy; we want
#     to work with the adjacency matrix for the asserted class hierarchy
# 1 - the 'union of powers' algorithm
# 2 - the Warshall algorithm
# 3 - OWL reasoning (via OWLRL)
transitive_closure_method = 3 

# specify whether or not to include the reflexive characteristic of the
# rdfs:subClassOf property in the adjacency matrix; if set to True, the
# result matrix will have 1s filling its diagonal
# 1 - the 'union of columns' algorithm
# 2 - relation composition via matrix multiplication
include_reflexivity = False 

# instantiate an OCHAM tool object
ocham = OCHAM(ontology_filename,
              transitive_closure_method=transitive_closure_method,
              include_reflexivity=include_reflexivity)

print('OCHAM object instantiated')                

#%% get the results

adjacency_matrix, classNames = ocham.get_results()

print('results retrieved')

#%% check number of classes

print(f'number of classes: {len(classNames)}')


#%% examine the class names

print('the class names')
print()

for name in classNames:
    print(name)


#%% check adjacency matrix shape

print(f'adjacency matrix shape: {adjacency_matrix.shape}')


#%% examine adjacency matrix

print('the adjacency matrix')
print()
print(adjacency_matrix)


#%% examine adjacency matrix 

print('some portion of the adjacency matrix')
print()
print(adjacency_matrix[0:6, 0:6])


#%% check the number of nonzero elements in the adjacency matrix

ordered_pairs = adjacency_matrix.nonzero()

print(f'number of nonzero elements: {len(ordered_pairs)}')


#%% examine the nonzero elements

print('the nonzero elements, e.g. (:A rdfs:subClassOf :B)')
print()
 
ochamu.show_encoded_triples(adjacency_matrix.nonzero(), classNames)






