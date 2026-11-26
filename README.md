# Clockcheck

Check whether rational timing constraints admit a shared timeline. Each
variable describes a true time. A difference bound constrains the difference
between two variables, and a clause offers one or more alternative bounds.

`solve(problem)` returns a rational assignment or `None`.
`minimal_conflict(problem)` returns the indices of an inclusion-minimal
contradiction. `clock_bounds(readings, accuracy)` adds the constraints for
a single clock, including ordering and equality for repeated readings.

The native solver searches alternatives and checks each conjunction by
relaxing difference bounds. A strict bound contributes a negative
infinitesimal. A zero-sum cycle with a strict bound is incompatible.
The solver chooses a positive rational infinitesimal small enough to keep
every positive rational slack, then shifts the assignment so the zero
variable is exactly zero.

The clock model assumes a nondecreasing map inside the declared error band.
A compatible assignment extends to the full timeline by linear interpolation
between distinct readings and by a constant offset outside the readings.
This is a conditional check of the declared model and input constraints.

Apache-2.0.

Copyright 2026 Mariia Steeghs-Turchina
