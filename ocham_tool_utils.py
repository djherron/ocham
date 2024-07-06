#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: David Herron
"""

'''
This module defines utility functions associated with the OCHAM tool.
'''

#%%

import torch

from owlrl import DeductiveClosure, OWLRL_Semantics

import networkx as nx


#%%

def show_encoded_triples(ordered_pairs, classNames):
    """
    Convert ordered pairs of integer indices into ordered pairs of
    class names, and print each ordered pair in both formats.
    
    We assume that the results are written to an IDE console window. To 
    make it easier to interpret the ordered pairs of class names within the
    confines of a console window, we shorten the class names by removing the 
    OWL ontology prefix. For example, long URI class names like
    http://example.com/ontologies/onto-01#someClass or
    http://example.com/ontologies/onto-01/someClass
    become short names like 'someClass'.
    """
    for pair in ordered_pairs:
        child_idx = pair[0]
        parent_idx = pair[1]
        child_name = classNames[child_idx]
        parent_name = classNames[parent_idx]
        
        hash_sign_present = '#' in child_name
        if hash_sign_present:
            child_name = child_name.split(sep='#')[1]
        else:
            child_name = child_name.split(sep='/')[-1]
        
        hash_sign_present = '#' in parent_name
        if hash_sign_present:
            parent_name = parent_name.split(sep='#')[1]
        else:
            parent_name = parent_name.split(sep='/')[-1]

        print(pair.numpy(), child_name, parent_name)
    
    return None


#%%

def get_uri(uriref):
    '''
    Extract an OWL URI from an RDFlib rdflib.term.URIRef object
    '''
    
    # extract the content of the rdflib.term.URIRef instance
    uri = uriref.n3()
    
    # remove the wrapping angle brackets introduced by the n3() function
    uri = uri.lstrip('<')
    uri = uri.rstrip('>')
    
    return uri


#%%

def transitive_closure_1(relation, extra_powers=0, verbose=0, patience=0,
                         early_stopping_active=True):
    '''
    Find the transitive closure of an homogeneous binary relation encoded
    as a binary matrix using what we call the 'union of powers' algorithm.
    
    If we let A denote the NxN binary matrix of a transitive binary 
    relation, and we let T denote the transitive closure of A, then
    
    T = UnionOf(A, A^2, A^3, A^4, ..., A^{N-1})
    
    where 'UnionOf' is the logical union of the sequence of binary power 
    matrices.
    
    In the vast majority of cases, a 'complete' transitive closure can
    be obtained by computing far fewer than the worst-case number of
    power matrices (N-1). We introduce an early stopping condition to
    capture these efficiencies. The early stopping condition is that the 
    union of the power matrices computed so far stops changing. We have
    identified three reasons why the union of the power matrices computed
    so far may stop changing. We report when early stopping has been
    invoked to stop the algorithm and we report the reason why.
    
    See "Relations and Graphs", Schmidt & Strohlein, section 3.2.1, pg 35,
    and see also pg 2 for important info and context for interpreting pg 35.
           
    Parameters
    ----------
    relation : 2D tensor
        The matrix of the relation whose transitive closure we wish to find.
    extra_powers : integer, optional
        A non-negative integer that represents an instruction to compute
        extra powers of the relation matrix that go beyond the upper bound
        of N-1.  This is for testing and curiosity.  It is redundant if
        the 'early stopping' mechanisms active.
    verbose : integer, optional
        An integer in the set {0,1,2} indicating the level of verbosity
        requested. Higher levels cause more print statements to fire.
    patience : integer, optional
        A non-negative integer that represents an instruction to continue
        computing power matrices even after the union matrix has stopped
        changing.  This is for testing mostly.
    early_stopping_active : boolean
        A logical flag indicating whether or not to apply early stopping
        to the algorithm, to minimise the number of powers computed.
    
    Returns
    -------
    tc : 2D tensor
        The transitive closure of the relation.
    alert : boolean
        A logical flag to indicate to the caller that the relation in 
        question leads to a violation of our hypothesis that once the
        union matrix stops changing, it always stays the same. The caller
        should analyse the relation matrix to understand how and why our
        hypothesis can be violated.
    '''
    
    power = relation
    N = relation.shape[0]
    n_elements = N * N
    union = relation
        
    previous_union = torch.zeros(N, N)
    
    # set the 'upper bound' for the number of powers to be computed
    # (if extra_powers > 0, this is an instruction to go beyond the normal 
    # upper bound on the number of powers computed, so we can inspect
    # the matrices of even higher powers, for testing and curiosity only)
    ub = N + extra_powers
    
    # initialise flags and counters
    cnt = 0
    successive_unions_equal = False
    we_can_stop = False
    alert = False
    
    # iteratively compute the powers of the relation matrix and form the
    # union (logical OR) of the relation and its successive powers
    for idx in range(2, ub):
        
        # compute the next power matrix
        power = torch.matmul(power, relation)
        power = torch.clamp(power, max=1.0)
        
        # union the current power matrix with the previous union
        union = union + power
        union = torch.clamp(union, max=1.0)

        if verbose > 0:
            print(f'power {idx}')
        if verbose > 1:
            print(power)
            print('union')
            print(union)
        
        # we have a hypothesis that once a union becomes identical to its
        # predecessor union, it never changes thereafter; this is equivalent
        # to the hypothesis that once nothing new is inferred, nothing new
        # will ever be inferred; the following code block helps us monitor
        # the validity of this hypothesis; it will point out exceptions
        # should they arise            
        if torch.equal(union, previous_union):
            if not successive_unions_equal and verbose > 0:
                print(f'union identical to predecessor, at power: {idx}')
            successive_unions_equal = True
        else:
            if successive_unions_equal and verbose > 0:
                print(f'union not identical to predecessor, at power: {idx}')
            if successive_unions_equal:
                alert = True 
            successive_unions_equal = False
        previous_union = union
        
        # if early stopping is NOT active, we can start the next iteration
        # of the 'for' loop; we want to bypass all the code that follows,
        # all of which has to do with early stopping
        if not early_stopping_active:
            continue

        # check early stopping conditions
        if successive_unions_equal:
            cnt += 1
            
            # if the power matrix is all zeros we can stop, because all
            # subsequent power matrices will also be all zeros
            if power.count_nonzero().item() == 0:
                if verbose > 0:
                    print('power is all zeros')
                we_can_stop = True
            
            # if the union matrix is all 1s we can stop, because the union 
            # relation has saturated (the universal relation) and there is
            # nothing left that can possibly be inferred
            elif union.count_nonzero().item() == n_elements:
                if verbose > 0:
                    print('union is all 1s')
                we_can_stop = True
            
            # otherwise, count the number of successive identical union
            # matrices we get and, when the patience is exceeded, stop.
            # 
            # note: this is scenario where our hypothesis could be flawed;
            # the union has stopped changing, but are we guaranteed it can
            # never change again due to some future power matrix?  we can't
            # prove our hypothesis, we can only disprove it by finding
            # cases that contradict it; that takes lots of testing
            else:
                # if we have exceed the patience, we stop (expediently)
                if verbose > 0:
                    print(f'identical union cnt: {cnt}, patience: {patience}')
                if cnt > patience:
                    if verbose > 0:
                        print('patience exceeded')
                    we_can_stop = True  # risk that results may not be 'complete'
        else:
            successive_unions_equal = False
            cnt = 0
        
        if we_can_stop:
            if verbose > 0:
                print('stopping early')
            break
    
    if verbose > 0:
        print(f'max power computed: {idx}, upper bound power: {N-1}')

    tc = torch.clamp(union, max=1.0)
    
    return tc, alert


#%%

def transitive_closure_2(relation, operation='boolean_OR'):
    '''
    Find the transitive closure of an homogeneous binary relation encoded
    as a binary matrix using Warshall's algorithm from graph theory.
    
    See "Relations and Graphs", Schmidt & Strohlein, section 3.2, pg 39
    '''
    
    N = relation.shape[0]
    
    mat = relation.detach().clone()
    
    if operation == 'boolean_OR':
    
        for col in range (0, N):
            for row in range (0, N):
                if mat[row, col] != 0:
                    for k in range(0, N):
                        mat[row, k] = mat[row, k] or mat[col, k]

    elif operation == 'add_and_clamp':

        for col in range (0, N):
            for row in range (0, N):
                if mat[row, col] != 0:
                    for k in range(0, N):
                        res = mat[row, k] + mat[col, k]
                        #res = torch.clamp(res, max=1.0)
                        mat[row, k] = res
    
        mat = torch.clamp(mat, max=1.0)
    
    else:
        
        raise ValueError(f'operation not recognised: {operation}')

    return mat


#%%

def transitive_closure_3(kg, classNames):
    '''
    Find the transitive closure of the rdfs:subClassOf class hierarchy
    asserted in an RDFlib KG using OWL reasoning.
    
    The OWL reasoning is performed by OWLRL.
    
    This method relies primarily on OWL reasoning, but it also uses 
    transitive closure method 1 to potentially infer edge cases that may
    have been missed by our use of OWL reasoning alone.
        
    With this method of finding the transitive closure of an OWL class
    hierarchy, it is easiest to build a fresh adjacency matrix from
    scratch.
    
    Summary of the transitive closure method implemented here:
    * a) use OWL reasoning to materialise the KG
    * b) build an initial adjacency matrix from all of the 
         (:A rdfs:subClassOf :B) triples where (:A != :B); that is, we 
         ignore all reflexive triples such as (:A rdfs:subClassOf :A);
         but note that by excluding all reflexive triples we may 
         inadvertently ignore some that arise naturally from transitivity
         reasoning (as opposed to reflexivity reasoning) due to cycles, 
         e.g. 2-cycles, in the graph of the ontology class hierarchy; such
         triples are valid members of the transitive closure, and belong in
         the adjacency matrix for the transitive closure; but we can't
         distinguish between reflexive triples inferred by OWL due to
         transitivity reasoning (rfds11) from those inferred by OWL due to 
         reflexivity reasoning (rdfs10); so rather than encode invalid 
         reflexive triples in our transitive closure adjacency matrix, we
         opt to exclude all reflexive triples at this stage
    * c) give the result (b) matrix to transitive closure method 1
         ('union of powers'); if the graph contains any cycles, these
         will lead to reflexive triples arising on the diagonal of
         result matrix (c); these are reflexive triples that were
         inadvertently excluded in (b) because we couldn't recognise that 
         they were inferred by transitivity rather than reflexivity;
         if the graph of the class hierarchy contains no cycles, the 
         matrix from (c) will be identical to that from (b); if cycles exist,
         result matrix (c) will be identical to that from (b) except for the
         presence of some reflexive triples on the diagonal
    * d) return result matrix (c)
    '''

    # configure the form of KG materialisation we wish to perform
    dc = DeductiveClosure(OWLRL_Semantics,
                          rdfs_closure = False,
                          axiomatic_triples = False,
                          datatype_axioms = False)

    # a) materialise the KG
    
    # note: all we need is the transitive closure of the rdfs:subClassOf
    # class hierarchy, but the only way to get this is to compute the
    # deductive closure of (i.e. materialise) the entire KG
    dc.expand(kg)

    # b) build transitive closure adjacency matrix using OWL reasoning
    
    # build a SPARQL query to get all of the triples that have
    # OWL construct rdfs:subClassOf as the predicate
    query = "SELECT ?sub ?obj WHERE { " + \
            "?sub rdfs:subClassOf ?obj . }"
    
    # execute the query
    qres = kg.query(query)
    
    # initialise an empty adjacency matrix for the transitive closure
    C = len(classNames)
    adj_mat = torch.zeros(C,C)
        
    # iterate over the result set and encode the (child-class, parent-class)
    # relationships that pertain to transitivity in an adjacency matrix;
    # (that is, we ignore any rdfs:subClassOf triples that arise from
    #  the reflexive characteristic of the rdfs:subClassOf property)
    for row in qres:
        child = get_uri(row.sub)
        parent = get_uri(row.obj)
        if child in classNames:
            child_idx = classNames.index(child)
            if parent in classNames:
                parent_idx = classNames.index(parent)
                if child_idx != parent_idx:  # i.e. ignore reflexive triples
                    adj_mat[child_idx, parent_idx] = 1.0             
    
    # c) call trans closure method 1 to infer any potential reflexive
    #    triples onto the diagonal of the adjacency matrix from (b)
    
    adj_mat2, alert = transitive_closure_1(adj_mat, extra_powers=0, 
                                           verbose=0, patience=0,
                                           early_stopping_active=True)  
        
    return adj_mat2


#%%

def find_longest_path(matrix, classNames, source_classNames, target_className):
    '''
    Find the longest (simple) path between source nodes and a target node.
    
    We use the Python package networkx to find all simple paths between
    the source nodes and the target node. Then we return one of the longest
    paths found along with its length.
    '''
     
    # convert the incoming matrix from a PyTorch tensor to a 2D numpy array
    matrix_np = matrix.numpy()
    
    # instantiate the adjacency matrix representing the OWL class hierarchy
    # as a networkx digraph
    G = nx.DiGraph(matrix_np)
    
    # convert the source class names to their integer indices
    start_nodes = []
    for name in source_classNames:
        class_idx = classNames.index(name)
        start_nodes.append(class_idx)
    
    # convert the target class name to its integer index
    target_node = classNames.index(target_className)
    
    # initialise the return variables
    a_longest_path_indices = None
    a_longest_path_names = []
    max_length = 0
    
    # iterate over the source nodes and find the longest path to the target
    for source_node in start_nodes:
        paths = nx.all_simple_paths(G, source_node, target_node)
        for path in paths:
            length = len(path)-1
            #print(f'{path} length: {length}')
            if length > max_length:
                max_length = length
                a_longest_path_indices = path
    
    if a_longest_path_indices != None:   
        for idx in a_longest_path_indices:
            a_longest_path_names.append(classNames[idx])
    
    return a_longest_path_names, a_longest_path_indices, max_length


#%%

def find_simple_cycles(matrix):
    
    # convert the incoming matrix from a PyTorch tensor to a 2D numpy array
    matrix_np = matrix.numpy()
    
    # instantiate the adjacency matrix representing the OWL class hierarchy
    # as a networkx digraph
    G = nx.DiGraph(matrix_np)    

    cycles = nx.simple_cycles(G)

    return cycles



