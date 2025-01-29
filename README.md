# How to run
- Install needed dependencies (find in pyproject.toml)
- run `python -m fhkart.main {target-ip}`
- You can also mock location data with `python -m fhkart.main {target-ip} --mock true`
- You can also change the track you want to play with `python -m fhkart.main {target-ip} --track-path={track-path}`

# Debug
- Enable debug logging with `LOGGING=DEBUG python -m fhkart.main {target-ip}`

# Requirements

-   GPS
-   Raspberry Pi am Fahrrad (2 Stück)
-   Rennen zu einem Punkt
-   Display welcher Platz man im Rennen ist

# Architecture

-   Push modell
-   On connect sends register with ip
-   Server sends updates to all registered ips
-   Every Server tracks time etc for itself
-   Always try to register new server
-   Drop Coordinates to sqlite
-   query sqlite if needed
