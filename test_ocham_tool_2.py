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

# ontologies G1, G2, G3, G4
ontology_filename = 'onto-G4.ttl'
url_base = "http://example.com/ontologies/onto-G1#"

# VRD-World ontology
#ontology_filename = 'vrd_world_v1.owl'
#url_base = "http://www.semanticweb.org/nesy4vrd/ontologies/vrd_world#"

# valid values:
# 1 - the 'union of powers' algorithm
# 2 - the Warshall algorithm
# 3 - OWL reasoning (via OWLRL)
transitive_closure_method = 3

if transitive_closure_method == 0:
    raise ValueError("ERROR: transitive closure required for this script's tests")

# specify whether or not to include the reflexive characteristic of the
# rdfs:subClassOf property in the adjacency matrix; if set to True,
# the tool fills the diagonal of the adjacency matrix with 1s
include_reflexivity = True 

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


#%% insert individual class membership triples for the set of classes

# For each named class in the class hierarchy, we insert a triple into the KG
# having the form: (:individual_nnnn rdf:type :namedClass)

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
print()
print('Example: (:individual_1234 rdf:type :someClass)')
print()
print(f'Number of triples inserted: {len(classNames)}')
print()
print(f'The KG now has {len(kg)} triples')


#%% get the individual class membership triples inserted into the KG

print('Retrieving individual triples from KG')
print()

query = """
        SELECT ?head ?tail
        WHERE {
            ?head rdf:type ?tail .
        }"""
    
# execute query
qres = kg.query(query)


#%% display the individual class membership triples inserted into the KG

print('Displaying information about the retrieved individual triples')
print()

show_triples = False

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

print('Inferring the deductive closure of the KG ...')
print()

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

print("Deductive closure of KG inferred by OWL reasoning")
print()
print(f'The KG now has {len(kg)} triples')


#%% display the class membership triples inferred for synthetic individuals

# NOTE: if the ontology uses anonymous classes to define classes in the
# class hierarchy, then our synthetic individuals may sometimes be inferred
# to be members of anonymous class (blank nodes) as well as named classes

class_idx_start = 3
class_idx_end = 7

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
            # ignore the (individual rdf:type childClass) triple that we
            # asserted and inserted into the KG; we don't want to list that
            # triple as having been inferred
            if parentClassName != childClassName: 
                print(parentClassName)
    

#%% retrieve the class membership inferred for all synthetic individuals

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



print('Retrieving class membership of individuals from KG ...')

# under all normal circumstances, we want to EXCLUDE BLANK NODES
# (i.e. anonymous classes); the OCHAM tool ignores anonymous classes and
# never encodes them in the adjacency matrix representations of the class
# hierarchies that it produces; so when working with the rdf:type class
# membership triples that OWL reasoning infers, we normally want to ignore
# blank nodes (anonymous classes) as well
exclude_blank_nodes = True

kg_results = {}

# iterate over the classes of the class hierarchy
for childClassIdx, childClassName in enumerate(classNames):

    # get the synthetic individual associated with the current class
    individual_name = individual_names[childClassIdx]
    
    # assemble a SPARQL query to get all of the 
    # (individual rdf:type someClass) triples for the current individual
    individual_uri = url_base + individual_name
    query = "SELECT ?tail WHERE { " + \
            "<" + individual_uri + ">" + " rdf:type ?tail . }"
    
    # execute the query
    qres = kg.query(query)
    
    # iterate over the query result set and extract the names of the classes
    # for which the current synthetic individual is a member in the
    # materialised KG
    kg_class_membership = []
    for row in qres:
        kgClassName = ochamu.get_uri(row.tail)
        if kgClassName.startswith('http://'):
            blank_node = False
        else:
            blank_node = True
        if blank_node and exclude_blank_nodes:
            continue
        
        # record that the individual is a member of the given class
        if not 'owl#' in kgClassName:
            record_class_membership = True
            if kgClassName == childClassName:  # (individual rdf:type childClass)
                if not include_reflexivity:
                    record_class_membership = False            
            if record_class_membership:
                kg_class_membership.append(kgClassName)

    kg_results[individual_name] = {'asserted_child_class': childClassName,
                                   'inferred_class_membership': kg_class_membership }

print()
print(f'Number of entries in KG results dictionary: {len(kg_results)}')


#%% perform the actual equivalence test

# Here we perform tests to verify that the adjacency matrix produced
# by the OCHAM tool agrees with a KG materialised via OWL reasoning.
#
# For each base class in the class hierarchy, we compare
#
# A) the parent classes encoded in the transitive closure adjacency matrix 
#    produced by the OCHAM tool
#
# with
#
# B) the parent classes inferred by OWL reasoning in a materialised KG 
#    for a synthetic individual asserted to be a member of the base class.
#    (That is, we focus on rdfs9 entailment, which infers a given
#    individual to be a member of all parent classes of some base class.)
#
# We do a bi-directional check. First we check that everything encoded
# in (A) is also recognised in (B), and then we check that everything
# recognised in (B) is encoded in (A).
#
# Any discrepancies between (A) and (B) detected in the bi-directional
# checks are reported to the console.

# Users of the OCHAM tool may request that reflexivity be reflected in the
# adjacency matrix by setting 'include_reflexivity = True'. In this case,
# the adjacency matrix will have 1s filling its entire diagonal.
#
# But reflexive relationships arise naturally from transitivity inference 
# alone if the graph of a class hierarchy contains cycles. Thus, even if
# the user specifies 'include_reflexivity = False', some reflexive class
# relationships may still appear on the diagonal of an adjacency matrix.
# We report any instances of this phenonenon that are detected, along with
# any instances of discrepancies that are detected.


nclasses = len(classNames)

discrepancy_count = 0

if transitive_closure_method == 0:
    raise ValueError('ERROR: adjacency matrix does not encode a transitive closure')

if adjacency_matrix.shape[0] != nclasses or \
   adjacency_matrix.shape[1] != nclasses:
    raise ValueError('problem: adjacency matrix shape incorrect')

# iterate over the classes of the class hierarchy
for childClassIdx, childClassName in enumerate(classNames):
    
    # get the synthetic individual that was asserted to be a member
    # of the current class
    individual_name = individual_names[childClassIdx]
    
    # get the class information retrieved from the materialised KG in
    # relation to the current synthetic individual
    res = kg_results[individual_name]
    kg_asserted_class = res['asserted_child_class']
    kg_class_membership = res['inferred_class_membership']
    
    # get the row of the adjacency matrix corresponding to the current class
    adj_mat_child_class_row = adjacency_matrix[childClassIdx]
    
    # verify there is no mix-up in the extracted KG data
    if not kg_asserted_class == childClassName:
        raise ValueError('problem: data mis-structured')
    
    # from the child class row of the adjacency matrix, extract the
    # indices of all of its parent classes encoded there
    adj_mat_parent_class_idxs = adj_mat_child_class_row.nonzero()
    adj_mat_parent_class_idxs2 = adj_mat_parent_class_idxs.squeeze()
    adj_mat_parent_class_idxs3 = []   
    if adj_mat_parent_class_idxs.shape[0] > 0:
        if adj_mat_parent_class_idxs.shape[0] == 1:
            adj_mat_parent_class_idxs3.append(adj_mat_parent_class_idxs2.item())
        else:
            for idx in adj_mat_parent_class_idxs2:
                adj_mat_parent_class_idxs3.append(idx.item())
    
    # Iterate over the parent classes encoded in the adjacency matrix 
    # for the current child class. Check that each adj_mat parent class
    # is recognised in the materialised KG as a parent class of the 
    # current child class.
    for parentClassIdx in adj_mat_parent_class_idxs3:
        
        adj_mat_parentClassName = classNames[parentClassIdx]
        
        adj_mat_parent_is_child = False
        if parentClassIdx == childClassIdx:
            adj_mat_parent_is_child = True
        
        discrepancy = False
        transitive_induced_reflexivity = False       
        if not adj_mat_parentClassName in kg_class_membership:
            discrepancy = True
            if adj_mat_parent_is_child and not include_reflexivity:
                discrepancy = False
                transitive_induced_reflexivity = True
       
        if discrepancy:
            discrepancy_count += 1
            print()
            print('DISCREPANCY:')
            print('The OCHAM tool adjacency matrix says child class')
            print(f'{childClassIdx} {childClassName}')
            print('has parent class')
            print(f'{parentClassIdx} {classNames[parentClassIdx]}')
            print('but the materialised KG disagrees.  It recognises individual')
            print(f'{individual_name}')
            print('as a member of the child class but not of the parent class.')

        if transitive_induced_reflexivity:
            print()
            print('TRANSITIVITY INDUCED REFLEXIVITY:')
            print('The OCHAM tool adjacency matrix says child class')
            print(f'{childClassIdx} {childClassName}')
            print('has parent class')
            print(f'{parentClassIdx} {classNames[parentClassIdx]}')
            print('which is reflexivity arising from transitivity.')            

    
    # for the current child class, check that each of its parent classes
    # as recognised by OWL reasoning is encoded as a parent class in the
    # adjacency matrix        
    for className in kg_class_membership:
        if className.startswith('http://'):
            blank_node = False
        else:
            blank_node = True
        if blank_node:  # ignore blank nodes (anonymous classes), if present
            continue
        classIdx = classNames.index(className)
        if not classIdx in adj_mat_parent_class_idxs3:
            discrepancy_count += 1
            print()
            print('DISCREPANCY:')
            print('The materialised KG says members of child class')
            print(f'{childClassIdx} {childClassName}')
            print('have parent class')
            print(f'{parentClassIdx} {classNames[parentClassIdx]}')
            print('but the OCHAM tool adjacency matrix does not agree.')   


if discrepancy_count > 0:
    print()
    print('Discrepancies detected between the adjacency matrix and')
    print('the materialised KG.')
    print()
    print(f'Number of discrepancies detected: {discrepancy_count}')
    print()
else:
    print()
    print('The adjacency matrix agrees with the materialised KG.')
    print()
    print(f'Number of discrepancies detected: {discrepancy_count}')
    print()   



