# Changelog
This project adheres to [Semantic Versioning](http://semver.org/).

## tag: 0.1.0 / 2021-09-14
- First working release


## tag: 0.2.0 / 2022-07-10
- Bugfix: Fixed a dependency version issue with `werkzeug`, #3
    - Using `poetry` for package and dependency management.
    - As of this verison, all dependencies are locked.
- Added `nr-wg-mtu-finder-heatmap` script for generating heatmap from the log file.
    - This script comes in handy if the original `nr-wg-mtu-finder` crashes mid way. Then a heatmap can be generated from the partial log file (csv) too, barring formatting issues of the log file.
- Formatted with black (88 linewidth) and isort (profile=black)
- First release to pypi so it can be installed with `pip install nr-wg-mtu-finder==0.2.0 --upgrade`