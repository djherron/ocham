#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: David Herron
"""

'''
This script demonstrates that a binary adjacency matrix produced by the
OCHAM tool faithfully encodes the transitive closure of an OWL ontology's
class hierarchy.  It demonstrates this by showing, for every class in
an OWL ontology class hierarchy, that the adjacency matrix for the transitive  
closure of the class hierarchy encodes the very same parent classes as
OWL reasoning infers.
'''

#%%

from ocham_tool import OCHAM

import ocham_tool_utils as ochamu

from rdflib import Graph
from rdflib.term import URIRef
from rdflib.namespace import RDF

from owlrl import DeductiveClosure, OWLRL_Semantics


#%% instantiate an OCHAM tool object

#ontology_filename = 'onto-G4.ttl'
ontology_filename = 'vrd_world_v1.owl'

# the base prefix (@base) used in the ontologies G1, G2, G3, G4
#url_base = "http://example.com/ontologies/onto-G1#"

# the base prefix (@base) used in the ontology vrd_world_v1.owl
url_base = "http://www.semanticweb.org/nesy4vrd/ontologies/vrd_world#"

# valid values:
# 0 - do not compute the transitive closure of the class hierarchy; we want
#     to work with the adjacency matrix for the asserted class hierarchy
# 1 - the 'union of powers' algorithm
# 2 - the Warshall algorithm
# 3 - OWL reasoning (via OWLRL)
transitive_closure_method = 3

if transitive_closure_method == 0:
    raise ValueError('ERROR: transitive closure required for this test script')

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

print('OCHAM tool object instantiated')                


#%% get the results

adjacency_matrix, classNames = ocham.get_results()

print('OCHAM tool results retrieved')
print()
print(f'Number of classes: {len(classNames)}')
print()
print(f'Adjacency matrix shape: {adjacency_matrix.shape}')


#%%

kg = Graph()

print("KG instantiated")
print(f'The KG now has {len(kg)} triples')

kg.parse(ontology_filename, format='ttl')

print()
print(f"Ontology '{ontology_filename}' loaded into KG")
print(f'The KG now has {len(kg)} triples')


#%% insert individual class membership triple for a set of classes

individual_base_name = 'individual_'

nclasses = len(classNames)

width = len(str(nclasses)) + 1

individual_names = []

# insert one triple into the KG for each class; the triple asserts that
# a synthetic individual is a member of that class
for idx, className in enumerate(classNames):
    individual_name = individual_base_name + str(idx).zfill(width)
    
    individual_uriref = URIRef(url_base + individual_name)
    
    className_uriref = URIRef(className)
    
    triple = (individual_uriref, RDF.type, className_uriref)
    
    kg.add(triple)
    
    individual_names.append(individual_name)

print('Triples asserting one unique individual per class inserted into KG')
print('Example: :individual_1234 rdf:type :someClass')
print(f'Number of triples inserted: {len(classNames)}')
print(f'The KG now has {len(kg)} triples')


#%% get the individual class membership triples inserted into the KG

query = """
        SELECT ?head ?tail
        WHERE {
            ?head rdf:type ?tail .
        }"""
    
# execute query
qres = kg.query(query)

print(f'Number of rdf:type triples retrieved from KG: {len(qres)}')


#%% display the individual class membership triples inserted into the KG

show_triples = True

show_blank_nodes = False

triples_for_named_classes_count = 0
triples_for_anonymous_classes_count = 0

# iterate over the query result set 
for row in qres:
    
    head_uri = ochamu.get_uri(row.head)
    if '#' in head_uri:
        head = head_uri.split(sep='#')[1]
    else:
        head = head_uri.split(sep='/')[-1]
    
    # accept only triples where the head is one of the synthetic
    # individuals that we inserted into the KG
    if not head.startswith('individual_'):
        continue
    
    tail_uri = ochamu.get_uri(row.tail)   
        
    # ignore triples like (:individual_nnnn rdf:type owl#Thing)
    if 'owl#' in tail_uri:
        continue
 
    if tail_uri.startswith('http://'):
        blank_node = False
        if '#' in tail_uri:
            tail = tail_uri.split(sep='#')[1]
        else:
            tail = tail_uri.split(sep='/')[-1]
    else:
        blank_node = True
        tail = tail_uri   

    if blank_node:
        triples_for_anonymous_classes_count += 1
    else:
        triples_for_named_classes_count += 1
    
    # display the triple (without rdf:type in the middle)
    if not blank_node or show_blank_nodes:
        if show_triples:
            print(head, tail)

print()
print(f'Number of (:individual rdf:type :namedClass) triples: {triples_for_named_classes_count}')
print()
print(f'Number of (:individual rdf:type :blankNode) triples: {triples_for_anonymous_classes_count}')

#%%

# configure the form of KG materialisation we wish to perform
dc = DeductiveClosure(OWLRL_Semantics,
                      rdfs_closure = False,
                      axiomatic_triples = False,
                      datatype_axioms = False)

# materialise the KG
#
# note: all we need is for OWL to perform the inference semantics of
# RDFS entailment rules rdfs9, rdfs10, and rdfs11, but the only way to 
# activate that reasoning is to compute the deductive closure (i.e.
# materialise) the entire KG
dc.expand(kg)

print("The deductive closure of the KG has been inferred by OWL reasoning")
print(f'The KG now has {len(kg)} triples')


#%% retrieve the class membership triples inferred for synthetic individuals

# NOTE: if the ontology uses anonymous classes to define classes in the
# class hierarchy, then our synthetic individuals may sometimes be inferred
# to be members of anonymous class (blank nodes) as well as named classes

class_idx_start = 10
class_idx_end = 14

if class_idx_end > len(classNames):
    raise ValueError('range of class index values is invalid')

for idx in range(class_idx_start, class_idx_end):
    
    # assemble a SPARQL query to get all of the rdf:type triples for
    # the current individual
    individual_name = individual_names[idx]
    individual_uri = url_base + individual_name
    query = "SELECT ?tail WHERE { " + \
            "<" + individual_uri + ">" + " rdf:type ?tail . }"

    # execute the query
    qres = kg.query(query)
    
    print()
    print(f'individual: {individual_name}')
    print(f'asserted to be a member of class idx: {idx}')
    childClassName = classNames[idx]
    print(childClassName)
    print('inferred to also be a member of parent classes:')
    
    # iterate over the query result set to get the classes for which
    # the current individual has been inferred to be a member
    for row in qres:
        parentClassName = ochamu.get_uri(row.tail)
        if not 'owl#' in parentClassName:
            if parentClassName != childClassName: 
                print(parentClassName)
    

#%% retrieve the class membership triples inferred for all synthetic individuals

#
# structure of kg_results dictionary of dictionaries
#
#kg_results = {'individual_009': {'asserted_child_class': 'onto-G1#J',
#                                 'inferred_parent_classes': ['onto-G1#F',
#                                                             'onto-G1#C',
#                                                             'onto-G1#A',] } }
#

# For each synthetic individual :x that we inserted into the KG, we extract
# all triples (:x rdf:type :Class) from the materialised KG. We store
# the individual, the base class of which the individual was asserted to
# be a member, and any other parent classes inferred by OWL reasoning during
# materialisation for that individual.
#
# NOTE: In our extracted results, we never store an asserted_child_class
# as a parent of itself, in the list of inferred_parent_classes. This has
# implications later, when we demonstrate equivalence of the adjacency
# matrix and OWL class membership reasoning.  See note in next section about
# this issue in connection with the user's possible use of the 
# 'include_reflexivity' configuration parameter when using the OCHAM tool
# to create the adjacency matrix.

# under all normal circumstances, we want to EXCLUDE BLANK NODES
# (i.e. anonymous classes); the OCHAM tool ignores anonymous classes and
# never encodes them in the adjacency matrix representations of the class
# hierarchies that it produces; so when working with the rdf:type class
# membership triples that OWL reasoning infers, we normally want to ignore
# blank nodes (anonymous classes) as well
exclude_blank_nodes = True

kg_results = {}

for childClassIdx, childClassName in enumerate(classNames):

    # assemble a SPARQL query to get all of the rdf:type triples for
    # the current individual
    individual_name = individual_names[childClassIdx]
    individual_uri = url_base + individual_name
    query = "SELECT ?tail WHERE { " + \
            "<" + individual_uri + ">" + " rdf:type ?tail . }"
    
    # execute the query
    qres = kg.query(query)
    
    # iterate over the query result set to get the classes for which
    # the current individual has been inferred to be a member
    parent_class_membership = []
    for row in qres:
        parentClassName = ochamu.get_uri(row.tail)
        if parentClassName.startswith('http://'):
            blank_node = False
        else:
            blank_node = True
        if blank_node and exclude_blank_nodes:
            continue
        if not 'owl#' in parentClassName:
            if parentClassName != childClassName: 
                parent_class_membership.append(parentClassName)

    kg_results[individual_name] = {'asserted_child_class': childClassName,
                                   'inferred_parent_classes': parent_class_membership }

print()
print(f'Number of entries in KG results dictionary: {len(kg_results)}')


#%% compare the parents in the adjacency matrix with the parents inferred by OWL

nclasses = len(classNames)

discrepancy_count = 0

if transitive_closure_method == 0:
    raise ValueError('ERROR: adjacency matrix does not encode a transitive closure')

if adjacency_matrix.shape[0] != nclasses or \
   adjacency_matrix.shape[1] != nclasses:
    raise ValueError('problem: adjacency matrix shape incorrect')

for childClassIdx, childClassName in enumerate(classNames):

    individual_name = individual_names[childClassIdx]

    res = kg_results[individual_name]
    kg_asserted_class = res['asserted_child_class']
    kg_parent_classes = res['inferred_parent_classes']
        
    adj_mat_child_class_row = adjacency_matrix[childClassIdx]
    
    if not kg_asserted_class == childClassName:
        raise ValueError('problem: data mis-structured')
    
    adj_mat_parent_class_idxs = adj_mat_child_class_row.nonzero()
    adj_mat_parent_class_idxs2 = adj_mat_parent_class_idxs.squeeze()
    adj_mat_parent_class_idxs3 = []   
    if adj_mat_parent_class_idxs.shape[0] > 0:
        if adj_mat_parent_class_idxs.shape[0] == 1:
            adj_mat_parent_class_idxs3.append(adj_mat_parent_class_idxs2.item())
        else:
            for idx in adj_mat_parent_class_idxs2:
                adj_mat_parent_class_idxs3.append(idx.item())
    
    #print(f'child: {childClassIdx}')
    #print(f'parents: {adj_mat_parent_class_idxs3}')    
    #print()
    
    # for the current child class, check that each of its parent classes
    # encoded in the adjacency matrix is recognised as a parent class by
    # OWL reasoning
    for parentClassIdx in adj_mat_parent_class_idxs3:
        className = classNames[parentClassIdx]
        if not className in kg_parent_classes:
            # if the user opted to 'include_reflexivity' in the adjacency matrix,
            # along with the transitive closure of the class hierarchy, then
            # we will encounter reflexive parents in the adjacency matrix;
            # the kg_results dictionary does not store reflexive parents, so
            # we must take care to avoid reporting a discrepancy in this
            # special edge case
            if childClassIdx == parentClassIdx and not include_reflexivity:
                discrepancy_count += 1
                print()
                print('DISCREPANCY:')
                print('child class')
                print(f'{childClassIdx} {childClassName}')
                print('has parent class')
                print(f'{parentClassIdx} {classNames[parentClassIdx]}')
                print('in the adjacency matrix, but OWL reasoning')
                print('does not recognise this as a parent class')
    
    # for the current child class, check that each of its parent classes
    # as recognised by OWL reasoning is encoded as a parent class in the
    # adjacency matrix        
    for parentName in kg_parent_classes:
        if parentName.startswith('http://'):
            blank_node = False
        else:
            blank_node = True
        if blank_node:  # ignore blank nodes (anonymous classes), if present
            continue
        parentClassIdx = classNames.index(parentName)
        if not parentClassIdx in adj_mat_parent_class_idxs3:
            discrepancy_count += 1
            print()
            print('DISCREPANCY:')
            print('child class')
            print(f'{childClassIdx} {childClassName}')
            print('has parent class')
            print(f'{parentClassIdx} {classNames[parentClassIdx]}')
            print('that is recognised by OWL reasoning, but that is not')
            print('encoded as a direct parent in the adjacency matrix')    

if discrepancy_count > 0:
    print()
    print('Discrepancies detected between the adjacency matrix and the')
    print('class hierarchy as inferred by OWL reasoning in the KG.')
    print()
    print(f'Number of discrepancies detected: {discrepancy_count}')
    print()
else:
    print()
    print('The adjacency matrix encodes the transitive closure')
    print('of the OWL ontology class hierarchy correctly!')
    print()
    print(f'Number of discrepancies detected: {discrepancy_count}')
    print()   


