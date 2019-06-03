"""Package regrouping all the possible modifications.

It already contains some basic modifications that can be used by default.
For any new custom modification, they should be added in this package in
order to be properly by the engine later. The discovery of new modifications
should be automatic.

There is one slightly different module in this package: `mod`. It is used to
define `Mod`, the base class for any modifications. This is an abstract class.
To write new modifications, one should subclass `Mod` and implements all the
abstract methods.
"""
