# NICE

## A NICE way to test OpenFlow controller applications

NICE is a tool to test OpenFlow controller application for the NOX controller platform through a combination of model checking and symbolic execution.

The emergence of OpenFlow-capable switches enables exciting new network functionality, at the risk of programming errors that make communication less reliable. The centralized programming model, where a single controller program manages the network, seems to reduce the likelihood of bugs. However, the system is inherently distributed and asynchronous, with events happening at different switches and end hosts, and inevitable delays affecting communication with the controller. In this paper, we present efficient, systematic techniques for testing unmodified controller programs. Our NICE tool applies model checking to explore the state space of the entire system—the controller, the switches, and the hosts. Scalability is the main challenge, given the diversity of data packets, the large system state, and the many possible event orderings. To address this, we propose a novel way to augment model checking with symbolic execution of event handlers (to identify representative packets that exercise code paths on the controller). Our prototype tests Python applications on the popular NOX platform.

## Quickstart

To quickly start finding bugs in the pyswitch sources:

$ cd ./nice
$ ./run_demo.sh

## Documentation

The documentation for NICE is available at: https://github.com/mcanini/nice/wiki

