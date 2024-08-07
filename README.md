# The OCHAM tool

OCHAM = OWL class hierarchy adjacency matrix

The OCHAM tool consumes an OWL ontology and produces a (binary) adjacency matrix that encodes the class hierarchy defined in the ontology.  It returns the matrix and the list of OWL class names extracted from the ontology that was used to construct the matrix.  The list of class names is needed to interpret the matrix.

## Files associated with the OCHAM tool

ocham_tool.py
* a module that defines the Python class that is the core of the OCHAM tool

ocham_tool_utils.py
* a module that defines some utility functions associated with the OCHAM tool

test_ocham_tool.py
* a script that doubles as 1) a driver for testing the OCHAM tool, and 2) an example of how to use the OCHAM tool and how to inspect the results that it returns.
* this script is designed to be run interactively in an IDE that recognises code sections delimited with `#%%` markers; execute a section and review the results written to the IDE's console window
* `get_results()` returns a) an adjacency matrix, and b) the list of class names used to construct and interpret the adjacency matrix
* `get_longest_path()` returns a longest path in the class hierarchy and the length of this longest path

test_ocham_tool_2.py
* a script that verifies that the adjacency matrix produced by the OCHAM tool agrees with the deductive closure of a KG materialsed with OWL reasoning

onto-01.ttl
* an OWL ontology that defines nothing but a simple class hierarchy

onto-G1.ttl
onto-G2.ttl
onto-G3.ttl
onto-G4.ttl
* a series of OWL ontologies that define variations of a simple class hierarchy
* the class hierarchy of G2 extends G1; G3 extends G2; and G4 extends G3
* G4 contains a 2-cycle (two classes that are rdfs:subClassOf one another)

vrd_world_v1.owl
* a copy of the VRD-World ontology (in turtle format, despite the '.owl' suffix)
* this is a larger, more complex ontology with 239 classes in its class hierarchy

## Dependencies

Python packages:
* PyTorch
* RDFlib
* OWLRL
* NetworkX

## Functionality

The OCHAM tool allows the user to specify the desired characteristics of the adjacency matrix to be produced to encode the class hierarchy of an OWL ontology.

The OCHAM tool consumes the ontology and produces the adjacency matrix at instantiation. The adjacency matrix and the list of class names used to construct it are obtained via the API call `get_results()`.

#### Transitivity 

The user may request an adjacency matrix that encodes either 1) the **asserted** class hierarchy only (i.e. the one declared explicitly in the OWL ontology file) or 2) the **transitive closure** of the class hierarchy.

Three algorithms are available for calculating transitive closures:
* the 'union of powers' algorithm
* Warshall's algorithm
* OWL reasoning

#### Reflexivity

The user may also request that the adjacency matrix reflects the **reflexive** characteristic of OWL's `rdfs:subClassOf` construct.  Reflexivity can be requested in relation to either the **asserted** class hierarchy or the **transitive closure** of the class hierarchy. A transitive closure that includes full reflexivity is sometimes called a reflexive-transitive closure.

#### Longest paths

The OCHAM tool can also find longest paths in the class hierarchy declared in the OWL ontology. Given a list of source class names, and a target class name, the API call `get_longest_path()` will return an instance of a longest path in the class hierarchy along with the length of this longest path.

#### Cycles

The OCHAM tool can also find simple cycles in the graph of the class hierarchy that it encodes in the adjacency matrix it produces.  A simple cycle is a closed path where no class (graph node) appears twice (except for the initial and final nodes, which close the path). Use the API call `get_simple_cycles()` to check for cycles.

A 1-cycle is a cycle of length 1. For example, `(:A rdfs:subClassOf :A)` is a 1-cycle. These 1-cycles (or reflexive relationships, or self-loops), if they exist in the graph, appear on the diagonal of the adjacency matrix. A 2-cycle is a cycle of length 2. For example, a pair of triples `(:A rdfs:subClassOf :B)` and `(:B rdfs:subClassOf :A)` represents a 2-cycle.

If a $k$-cycle, for $k > 1$, exists in the graph of a class hierarchy, inference of the transitive closure leads to inference of a 1-cycle (self-loop) for each of the $k$ elements involved in the cycle.  For instance, our example 2-cycle would lead to 1-cycles `(:A rdfs:subClassOf :A)` and `(:B rdfs:subClassOf :B)` being represented on the diagonal of the OCHAM tool's adjacency matrix.  In other words, if a graph contains cycles, transitivity reasoning will naturally produce (valid) reflexive results. 


## Limitations

The OCHAM tool has some nuances and limitations. We discuss these here.

The OCHAM tool currently sorts the class names extracted from the OWL ontology file in alphabetic order.  The structure of the adjacency matrix is determined by this alphabetic ordering of class names.  If the user desires a different ordering of the class names, currently the user must manually adjust the order of the names in the list of class names and, crucially, adjust the order of the rows of the adjacency matrix correspondingly.

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
When the OCHAM tool builds the adjacency matrix for the **asserted** class hierarchy (the one declared explicitly in the OWL ontology file), it will fail to identify these two implicit `rdfs:subClassOf` axioms.  As a result, if the adjacency matrix for the **transitive closure** of the class hierarchy has been requested by the user, and the transitive closure is computed without using OWL reasoning, then the transitive closure will be incomplete, and hence the adjacency matrix for the transitive closure will be incomplete. In such cases, the user can opt to have the transitive closure computed by OWL reasoning. OWL reasoning will infer the two implicit `rdfs:subClassOf` axioms and make them explicit, along with any other `rdfs:subClassOf` axioms entailed by them. Thus, the adjacency matrix constructed for the transitive closure of the class hierarchy will include these two (previously implicit) `rdfs:subClassOf` axioms as well as any other `rdfs:subClassOf` axioms entailed by them.






