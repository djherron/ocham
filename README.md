# README

This document provides guidance regarding:
* the OCHAM tool
* designing OWL ontologies for use with the OCHAM tool

# The OCHAM tool

OCHAM = OWL class hierarchy adjacency matrix

the OCHAM tool consumes an OWL ontology and produces an adjacency matrix that encodes the class hierarchy defined in that ontology

## files associated with the OCHAM tool

ocham_tool.py
* a module that defines the Python class that is the core of the OCHAM tool

ocham_tool_utils.py
* a module that defines some utility functions associated with the OCHAM tool

test_ocham_tool.py
* a script that doubles as 1) a driver for testing the OCHAM tool, and 2) an example of how to use the OCHAM tool and how to inspect the results that it returns: a) an adjacency matrix, and b) the list of class names used to construct and interpret the adjacency matrix
* this script is designed to be run interactively in an IDE that recognises code sections delimited with `#%%` markers; execute a section and review the results written to the IDE's console window

onto-01.ttl
* an OWL ontology that defines nothing but a simple class hierarchy

README.md
* this file, the file you are reading


# Dependencies

Python packages:
* PyTorch
* RDFlib
* OWLRL


# OWL ontologies and the OCHAM tool

The OCHAM tool has some nuances and limitations. We discuss these here.

The OCHAM tool currently assumes that the OWL ontology to be processed is expressed in turtle (`.ttl`) syntax. This can be adjusted in function `load_ontology()` in module `ocham_tool.py`.

The OCHAM tool currently ignores anonymous OWL classes (blank nodes). Thus, the most accurate results are obtained if one uses the OCHAM tool with OWL ontologies whose class hierarchies are designed strictly in terms of named classes which are not defined with respect to arbitrary class expressions.

















