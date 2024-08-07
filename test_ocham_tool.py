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
#ontology_filename = 'onto-G1.ttl'
ontology_filename = 'vrd_world_v1.owl'

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
transitive_closure_method = 0

# specify whether or not to include the reflexive characteristic of the
# rdfs:subClassOf property in the adjacency matrix; if set to True,
# the tool fills the diagonal of the adjacency matrix with 1s
include_reflexivity = False 

# instantiate an OCHAM tool object
ocham = OCHAM(ontology_filename,
              transitive_closure_method=transitive_closure_method,
              include_reflexivity=include_reflexivity)

print('OCHAM tool object instantiated')                

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


#%% longest paths

#%% find a longest path between source classes and a target class

# classes that apply to ontologies (graphs) G1, G2, G3 and G4
#source_classNames = ['http://example.com/ontologies/onto-G1#G',
#                     'http://example.com/ontologies/onto-G1#H',
#                     'http://example.com/ontologies/onto-G1#I',
#                     'http://example.com/ontologies/onto-G1#J',
#                     'http://example.com/ontologies/onto-G1#K' ]

# top-most class in the class hierarchy of ontologies (graphs) G1, G2, G3, G4
#target_className = 'http://example.com/ontologies/onto-G1#A'

# classes that apply to ontology vrd_world_v1.owl
source_classNames = ['http://www.semanticweb.org/nesy4vrd/ontologies/vrd_world#Shoe',
                     'http://www.semanticweb.org/nesy4vrd/ontologies/vrd_world#Tree',
                     'http://www.semanticweb.org/nesy4vrd/ontologies/vrd_world#WasteBin']

# top-most class in the class hierarchy of ontology vrd_world_v1.owl
target_className = 'http://www.semanticweb.org/nesy4vrd/ontologies/vrd_world#VRDWorldThing'

# find a longest simple path between the set of source classes and
# the target class; a 'simple' path is one with no repeated nodes
res = ocham.get_longest_path(source_classNames, target_className)
longest_path_names = res[0]
longest_path_indices = res[1]
longest_path_length = res[2]

# display the results
print('longest path results retrieved')
print()
print('a longest simple path:')
for name in longest_path_names:
    print(name)
print()
print('the same longest simple path as integer indices:')
print(longest_path_indices)
print()
print(f'length of longest simple path: {longest_path_length}')


#%% cycles

#%% find simple cycles in the graph of the class hierarchy

# A simple cycle is a closed path where no node appears twice (except for
# the initial and final nodes, which close the path).
#
# The simplest cycle is a 1-cycle or self-loop
# e.g. (:X rdfs:subClassOf :X)
#
# The next simplest cycle is a 2-cycle 
# e.g. (:X rdfs:subClassOf :Y), (:Y rdfs:subClassOf :X).

print('Checking for cycles in the graph of the class hierarchy ...')
print()

cycles = ocham.get_simple_cycles()

cycle_count = 0
for cycle in list(cycles):
    cycle_count += 1
    print(cycle)

print()
print(f'Number of simple cycles found: {cycle_count}')


#%% check adjacency matrix for entries that encode 1-cycles (self-loops)

print('Checking for 1-cycles on diagonal of adjacency matrix ...')
print()

self_loop_count = 0
for idx in range(len(classNames)):
    if adjacency_matrix[idx,idx] == 1.0:
        self_loop_count += 1
        print(f'[{idx},{idx}]')

print()
print(f'Number of 1-cycles found: {self_loop_count}')



