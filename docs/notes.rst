Given a playlist of three tracks numbered 1, 2, 3, and a currently playing
track ``c``.

Tests perfomed on MPD 0.15.4-1ubuntu3.

======  ======  ======  =======  =====  =====  =====
            Inputs                  previous_track
-------------------------------  -------------------
repeat  random  single  consume  c = 1  c = 2  c = 3
======  ======  ======  =======  =====  =====  =====
T       T       T       T        Rand?  Rand?  Rand?
T       T       T       .        3      1      2
T       T       .       T        Rand?  Rand?  Rand?
T       T       .       .        3      1      2
T       .       T       T        3      1      2
T       .       T       .        3      1      2
T       .       .       T        3      1      2
T       .       .       .        3      1      2
.       T       T       T        c      c      c
.       T       T       .        c      c      c
.       T       .       T        c      c      c
.       T       .       .        c      c      c
.       .       T       T        1      1      2
.       .       T       .        1      1      2
.       .       .       T        1      1      2
.       .       .       .        1      1      2
======  ======  ======  =======  =====  =====  =====

======  ======  ======  =======  =====  =====  =====
            Inputs                    next_track
-------------------------------  -------------------
repeat  random  single  consume  c = 1  c = 2  c = 3
======  ======  ======  =======  =====  =====  =====
T       T       T       T      
T       T       T       .        
T       T       .       T      
T       T       .       .      
T       .       T       T      
T       .       T       .      
T       .       .       T      
T       .       .       .      
.       T       T       T      
.       T       T       .      
.       T       .       T      
.       T       .       .      
.       .       T       T      
.       .       T       .      
.       .       .       T      
.       .       .       .      
======  ======  ======  =======  =====  =====  =====

Other rules
-----------

- If :attr:`time_position` of the current track is 15s or more,
  :meth:`previous()` should do a :meth:`seek()` to time position 0.
