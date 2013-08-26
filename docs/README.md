python-protea
============

Ashly Audio DSP and products Python RS-232 interface library.

This library aims at providing a convenient and simple layer between a python
script and the RS-232 interface driving Ashly DSP products.


Available devices
-----------------

Class name  | Description
------------|----------------------
Protea      | Generic Protea device
P424C       | Protea 4.24C
Ne2424M     | Protea ne24.24M

As first parameter for these class, one must pass the name to the serial
interface (that will in turn get opened using the pyserial library), or a
serial interface object that supports `read`, `write`, `flushInput` and
`flushOutput` methods.

Protea, 4.24C and ne24.24M are trademarks of Ashly Audio Inc.
