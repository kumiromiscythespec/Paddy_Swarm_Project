# Failed / Superseded CAD Iterations

This directory intentionally keeps only the current printable/reviewable v228 restart files.

Older v2273/v2274/v227-restart prototype generators were removed from the public working tree because they caused one or more of the following issues:

- wrong BBOX/CBOX notch orientation
- oversized shell or belly hull parts
- floating-looking slicer islands
- internal support generation
- excessive material use
- confusing legacy shell/hull/sponson parts not fitted to the fixed core
- single PTO output before the v228.1 dual-output correction

The design decision is to protect users from accidentally printing obsolete hardware files.
Historical files are kept in local archive, not in the public release tree.