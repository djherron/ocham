# The OCHAM tool

OCHAM = OWL class hierarchy adjacency matrix

The OCHAM tool consumes an OWL ontology and produces a (binary) adjacency matrix that encodes the class hierarchy defined in the ontology.  It returns the matrix and the list of OWL class names extracted from the ontology that was used to construct the matrix.  The list of class names is needed to interpret the matrix.

**Table of Contents**
[TOC]



## Files associated with the OCHAM tool

ocham_tool.py
* a module that defines the Python class that is the core of the OCHAM tool

ocham_tool_utils.py
* a module that defines some utility functions associated with the OCHAM tool

test_ocham_tool.py
* a script that doubles as 1) a driver for testing the OCHAM tool, and 2) an example of how to use the OCHAM tool and how to inspect the results that it returns: a) an adjacency matrix, and b) the list of class names used to construct and interpret the adjacency matrix
* this script is designed to be run interactively in an IDE that recognises code sections delimited with `#%%` markers; execute a section and review the results written to the IDE's console window

onto-01.ttl
* an OWL ontology that defines nothing but a simple class hierarchy


## Dependencies

Python packages:
* PyTorch
* RDFlib
* OWLRL

## Functionality

The OCHAM tool

The OCHAM tool allows the user to specify the desired characteristics of the adjacency matrix to be produces to encode an OWL ontology class hierarchy in a binary adjacency matrix.


## Limitations

The OCHAM tool has some nuances and limitations. We discuss these here.

The OCHAM tool currently sorts the class names extracted from the OWL ontology file in alphabetic order.  The structure of the adjacency matrix is determined by this alphabetic ordering of class names.  If the user desires a different ordering of the class names, currently the user must manually adjust the order of the names in the list and, crucially, adjust the order of the rows of the adjacency matrix correspondingly.

The OCHAM tool currently assumes that the OWL ontology to be processed is expressed in turtle (`.ttl`) syntax. This can be adjusted in function `load_ontology()` in module `ocham_tool.py`.

The OCHAM tool currently ignores anonymous OWL classes (blank nodes). Thus, the most accurate results are obtained if one uses the OCHAM tool with OWL ontologies whose class hierarchies are designed strictly in terms of named classes which are not defined with respect to arbitrary class expressions.

Certain (limited) types of OWL class expressions are supported accurately, however, so long as the user requests that the adjacency matrix reflects the **transitive closure** of the class hierarchy AND requests that **OWL reasoning** be used to infer the transitive closure.  For example, suppose the class hierarchy of the OWL ontology defines a certain named class to be the intersection of two other named classes, using statements such as
```
:A rdf:type owl:Class .
:A owl:intersectionOf (:B :C) .
```
This declaration implies two `rdfs:subClassOf` axioms, as follows:
```
:A rdfs:subClassOf :B .
:A rdfs:subClassOf :C .
```
When the OCHAM tool builds the adjacency matrix for the **asserted** class hierarchy (the one declared explicitly in the OWL ontology file), it will fail to identify these two implicit `rdfs:subClassOf` axioms.  As a result, if the adjacency matrix for the **transitive closure** of the class hierarchy has been requested by the user, and the transitive closure is computed without using OWL reasoning, then the transitive closure will be incomplete, and hence the adjacency matrix for the transitive closure will be incomplete. In such cases, the user can opt to have the transitive closure computed by OWL reasoning. OWL reasoning will infer the two implicit `rdfs:subClassOf` axioms and make them explicit. Thus, when the adjacency matrix for the transitive closure of the class hierarchy is constructed, it will include these two `rdfs:subClassOf` axioms, and any other `rdfs:subClassOf` axioms entailed by them.













