Peerchat IRC Backend
============================================================

Description
-----------

This is a backend for Peerchat, which is a GameSpy service that allows simple and easy game to game chat. It is using the code of miniircd, a small and limited IRC server written in Python.

Features
--------
* Pokémon Generation 4 WFC Plaza support.

Usage
-----

To use this, you will first need to run the server itself on port 6668; `python miniircd --ports=6668`

Then, run aluigi's [peerchat server emulator](http://aluigi.altervista.org/papers.htm#peerchat) on port 6667.

Requirements
------------

Python 3.7, or newer. Get it at <https://www.python.org>.
Poetry, get it at <https://python-poetry.org/>.

License
-------

GNU General Public License version 2 or later.

Credits
-------
jrosdahl, for miniircd.
shutterbug2000, for RE of WFC Plaza, and recoding.
Mythra, for RE of WFC Plaza, recoding, and modernization.
pokeacer and larsenv, for testing.
