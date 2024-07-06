#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: David Herron
"""

'''
This module defines a Python class that implements what we call the
OWL class hierarchy adjacency matrix tool, or OCHAM tool.

It represents the class hierarchy defined in an OWL ontology file as an
adjacency matrix --- a square, binary matrix constructed according to a 
particular fixed ordering of the class names of the class hierarchy.

The OCHAM tool assumes that the ontology is in turtle (.ttl) format. 
This assumption can be adjusted in the function load_ontology(), below.

The OCHAM tool ignores anonymous OWL classes (blank nodes). It is thus best 
to use an OWL ontology whose class hierarchy consists strictly of classes
defined in terms of names alone, not in terms of class expressions (which
give rise to anonymous classes). 

Dependencies:
    PyTorch
    RDFlib
    OWLRL   (see ocham_utils)
'''

#%% imports

import torch

import ocham_tool_utils as ochamu

from rdflib import Graph


#%%

class OCHAM():
    
    def __init__(self, ontology_filename, 
                       transitive_closure_method=1,
                       include_reflexivity=False):
        
        super(OCHAM, self).__init__()
        
        # the name of the ontology being processed
        self.onto_filename = ontology_filename
        
        # the method to be used for finding the transitive closure of the
        # ontology's class hierarchy
        #
        # 0 = do not compute the transitive closure of the class hierarchy;
        #     instead, just return the adjacency matrix that corresponds
        #     to the class hierarchy explicitly asserted in the ontology
        # 1 = union of powers algorithm
        # 2 = Warshall's algorithm
        # 3 = OWL reasoning via OWLRL
        self.transitive_closure_method = transitive_closure_method
        
        # whether or not the user has requested that the reflexive
        # characteristic of the OWL rdfs:subClassOf property be 
        # included in the adjacency matrix of the OWL class hierarchy
        self.include_reflexivity = include_reflexivity
                
        # an attribute to hold an instance of an RDFlib KG; the OWL
        # ontology is loaded into this KG for subsequent processing
        self.kg = None
        
        # an ordered list of the class names (URIs) extracted from
        # the OWL ontology; let C denote the number of class names
        self.classNames = None
        
        # the adjacency matrix that encodes the asserted
        # class hierarchy of the OWL ontology
        self.adjacency_matrix_asserted = None     # CxC

        # the adjacency matrix that encodes the transitive closure
        # of the class hierarchy of the OWL ontology
        self.adjacency_matrix_transitive_closure = None  # CxC
        
        # the result adjacency matrix to be retrieved by the user
        self.result_matrix = None   # CxC
        
        # process the ontology and construct the adjacency matrix
        # of the ontology's class hierarchy
        self.process_the_ontology()
        
        return None

    
    def process_the_ontology(self):
        if not self.transitive_closure_method in [0, 1, 2, 3]:
            raise ValueError('transitive closure method not recognised')
        if not self.include_reflexivity in [True, False]:
            raise ValueError('include_reflexivity setting not recognised')
        self.instantiate_KG()
        self.load_ontology()
        self.get_KG_classes()
        self.build_asserted_class_hierarchy_adjacency_matrix()
        if self.transitive_closure_method > 0:
            self.build_class_hierarchy_transitive_closure_adjacency_matrix()
        if self.include_reflexivity:
            self.include_reflexivity_in_adjacency_matrix()
        self.set_result_matrix()
        return None

        
    def instantiate_KG(self):
        self.kg = Graph()
        return None

    
    def load_ontology(self):
        self.kg.parse(self.onto_filename, format='ttl')
        return None


    def get_KG_classes(self):
    
        # build SPARQL query
        query = """
                SELECT ?className 
                WHERE {
                    ?className rdf:type owl:Class .
                }"""
    
        # execute query
        qres = self.kg.query(query)
    
        classNames = []
        
        # iterate over the query result set to get the class names
        for row in qres:  
            className = ochamu.get_uri(row.className)   
            # if we have a valid URI, store the class URI (aka class name)
            if className.startswith('http://'):
                classNames.append(className)
        
        # ensure we have the top-level class, owl:Thing, in our list
        # of class names
        #
        # (Note: If we first materialised the KG, our query would pick 
        #  this up. But otherwise, it's usually not explictly declared 
        #  in an ontology file.)
        #owlThing_URI = 'http://www.w3.org/2002/07/owl#Thing'
        #if not owlThing_URI in classNames:
        #    classNames.append(owlThing_URI)
        
        # sort the classes alphabetically in ascending order
        classNames = sorted(classNames)
                
        self.classNames = classNames
                
        return None


    def build_asserted_class_hierarchy_adjacency_matrix(self):
        '''
        Encode the ontology's asserted rdfs:subClassOf class hierarchy
        in a binary adjacency matrix.

        Note: we ignore any rdfs:subClassOf triples that contain class
        names not already in our list of class names
        '''

        # initialise an empty adjacency matrix for encoding the
        # class hierarchy of the ontology
        C = len(self.classNames)
        adj_mat = torch.zeros(C,C)

        # build a SPARQL query to get all of the triples that have
        # OWL construct rdfs:subClassOf as the predicate
        query = "SELECT ?sub ?obj WHERE { " + \
                "?sub rdfs:subClassOf ?obj . }"
        
        # execute the query
        qres = self.kg.query(query)
        
        # iterate over the result set and encode each asserted
        # (child-class, parent-class) relationship in the 
        # adjacency matrix
        for row in qres:
            child = ochamu.get_uri(row.sub)
            parent = ochamu.get_uri(row.obj)
            if child in self.classNames:
                child_idx = self.classNames.index(child)
                if parent in self.classNames:
                    parent_idx = self.classNames.index(parent)
                    adj_mat[child_idx, parent_idx] = 1.0             
        
        # store the adjacency matrix of the asserted class hierarchy
        self.adjacency_matrix_asserted = adj_mat
               
        return None


    def build_class_hierarchy_transitive_closure_adjacency_matrix(self):
        
        adj_mat = self.adjacency_matrix_asserted
        
        if self.transitive_closure_method == 1:

            # set parameters for transitive closure method 1
            extra_powers = 0  # don't calculate any extra powers
            verbose = 0       # no print statements
            patience = 0      # stop early as soon as condition detected
            
            # infer transitive closure using 'union of powers' algorithm
            tc, alert = ochamu.transitive_closure_1(adj_mat,
                                                    extra_powers=extra_powers,
                                                    verbose=verbose, 
                                                    patience=patience)                                                       

            # if we encounter an adjacency matrix that leads to unexpected
            # behaviours in the union-of-powers algorithm, report this so
            # we can analyse the matrix to understand why
            if alert:
                print('ALERT: the adjacency matrix for the asserted class')
                print('hierarchy needs analysis; it leads to unexpected')
                print('behaviour during the union-of-powers algorithm for')
                print('finding the transitive closure.')

        elif self.transitive_closure_method == 2:
            
            # infer transitive closure using Warshall's algorithm
            tc = ochamu.transitive_closure_2(adj_mat)

        else:  # self.transitive_closure_method == 3
        
            # infer transitive closure using OWL reasoning
            tc = ochamu.transitive_closure_3(self.kg, self.classNames)            

        self.adjacency_matrix_transitive_closure = tc        

        return None


    def include_reflexivity_in_adjacency_matrix(self):
        '''
        Encode the fact that the rdfs:subClassOf property is reflexive
        in the adjacency matrix encoding the rdfs:subClassOf class
        hierarchy.
        
        Note: We do a logical union between the base adjacency matrix and
        a matrix encoding the reflexive characteristic.  The logical union
        is simulated by doing matrix addition followed by clamping the values
        in the result to a maximum value of 1.0.  The clamping guards against
        any values of 2.0 appearing in the result. This could arise if there
        are any 1s already on the diagonal of the base adjacency matrix.
        This is unlikely, but it could arise if, for some reason, reflexive
        rdfs:subClassOf axioms are explicitly asserted in the ontology file.
        '''
        
        # initialise an empty adjacency matrix for encoding the
        # reflexivity of the rdfs:subClassOf OWL construct
        C = len(self.classNames)
        reflexivity = torch.eye(C)  # the identity matrix
        
        # union the reflexive characteristic with the correct adjacency matrix
        if self.transitive_closure_method == 0:  # no transitive closure requested
            union = self.adjacency_matrix_asserted + reflexivity
            union = torch.clamp(union, max=1.0)
            self.adjacency_matrix_asserted = union
        else: # we computed a transitive closure
            union = self.adjacency_matrix_transitive_closure + reflexivity        
            union = torch.clamp(union, max=1.0)
            self.adjacency_matrix_transitive_closure = union
            
        return None
    
        
    def set_result_matrix(self):
        
        if self.transitive_closure_method == 0:  # no transitive closure requested
            self.result_matrix = self.adjacency_matrix_asserted
        else: # we computed a transitive closure
            self.result_matrix = self.adjacency_matrix_transitive_closure      
        
        return None


    def get_results(self):
        '''
        This is intended as an API call for the user. It's a convenient way
        to retrieve the desired results after first instantiating an
        OCHAM object.
        
        We return the result matrix along with the class names because the
        result matrix can only be interpreted by the user if the ordering
        of the OWL class names is known.
        '''
        
        return self.result_matrix, self.classNames

    
    def get_longest_path(self, source_classNames, target_className):
        '''
        Find the longest simple path in the OWL class hierarchy between
        a set of source class names and a single target class name.
        
        The source class names are normally expected to be leaf nodes in
        the class hierarchy, and the target class name is normally expected
        to be the top-most class in the hierarchy.

        Parameters
        ----------
        source_classNames : list of strings
            A list of class names from the ontology.
        target_className : string
            A class name from the ontology.

        Returns
        -------
        longest_path : list of integers
            A longest path found in the class hierarchy.
        longest_path_length : integer
            The length of the longest path found in the class hierarchy

        '''
               
        if len(source_classNames) == 0:
            raise ValueError('expected one or more source class names')
        
        for name in source_classNames:
            if not name in self.classNames:
                raise ValueError(f'source class name not recognised: {name}')
        
        if target_className == None:
            raise ValueError('expected one target class name')
            
        if not target_className in self.classNames:
            raise ValueError(f'target class name not recognised: {name}')
        
        res = ochamu.find_longest_path(self.result_matrix,
                                       self.classNames,
                                       source_classNames,
                                       target_className)
        longest_path_names = res[0]
        longest_path_indices = res[1]
        longest_path_length = res[2]
        
        return longest_path_names, longest_path_indices, longest_path_length


    def get_simple_cycles(self):
        '''
        Get all simple cycles in the graph
        
        A simple cycle is a closed path where no node appears twice.
        The simplest simple cycle is a self-loop (:X rdfs:subClassOf :X)
        The next simplest simple cycle is a 2-cycle, (:X rdfs:subClassOf :Y),
        and (:Y rdfs:subClassOf :X).
        '''
        
        cycles = ochamu.find_simple_cycles(self.result_matrix)
        
        return cycles
    
    
