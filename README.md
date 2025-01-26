
# Table of Contents

1.  [Requirements](#org444b3a3)
2.  [Architecture](#org4a61d90)
3.  [TODOS](#org9d5b324)
    1.  [threading](#orgfc62619)
    2.  [UI](#org86726e8)
    3.  [Change Threads to classes](#orga3fda6c)


<a id="org444b3a3"></a>

# Requirements

-   GPS
-   Raspberry Pi am Fahrrad (2 Stück)
-   Rennen zu einem Punkt
-   Display welcher Platz man im Rennen ist


<a id="org4a61d90"></a>

# Architecture

-   Push modell
-   Multiple rest apis
-   On connect sends register with ip to static default ip
-   Server sends updates to all registered ips
-   Every Server tracks time etc for itself
-   If server is not reachable n amount of times it is deregistered and will not receive updates
-   Always try to register new server
-   Drop Coordinates to sqlite
-   query sqlite if needed


<a id="org9d5b324"></a>

# TODOS


<a id="orgfc62619"></a>

## DONE threading


<a id="org86726e8"></a>

## TODO UI


<a id="orga3fda6c"></a>

## TODO Change Threads to classes

So i can abstract the database connection handling into it's own class

