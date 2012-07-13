
ManaClash

A certain trading card game engine in Python. 

This is a alpha release version, so don't excpect much of it yet...

Authors:
    Marek Schmidt <fregaham AT gmail DOT com>

http://manaclash.org

Prerequisites:
    python2.6
    twisted
    Autobahn

Installation Instructions

1. Install prerequisites

ManaClash is written in Python. The web interface uses the Autobahn library for websockets communication between the server and the web browser.

2. Prepare card rules

ManaClash only implements the MTG rules and doesn't contain information about any particular cards. The card information is parsed from the "oracle" text files.

* Go to the MTG Gatherer web site
* Select "Eight edition"
* Select "Text spoiler" output format
* copy the resulting text into a plain text (UTF-8 encoded) file named <code>oracle/8th_edition.txt</code>.

    Note that ManaClash currently only understand a subset of the 8th Edition, so the other editions and sets will not work very well.

The resulting file should look like this:

    Name:   Abyssal Specter
    Cost:   2BB
    Type:   Creature — Specter
    Pow/Tgh:    (2/3)
    Rules Text:     Flying
    Whenever Abyssal Specter deals damage to a player, that player discards a card.
    Set/Rarity:     ...
    %br
    Name:   Air Elemental
    Cost:   3UU
    Type:   Creature — Elemental
    Pow/Tgh:    (4/4)
    Rules Text:     Flying
    Set/Rarity:     ...

3. Prepare initial decks

Create text files, such as decks/deckname.txt (UTF-8 encoded) containing decks in the following format:

    20   Swamp
    4    Dark Banishing
    3    Megrim
    ...

The filename will be used as the deck name in the web client UI.

4. Start the command-line mc.py program to verify the cards are parsed correctly:

    python mc.py decks/deck1.txt decks/deck2.txt

5. You may now start the webserver, which binds to the port 8080 by default:

    python abserver.py

6. ManaClash should be running on http://localhost:8080

ManaClash is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ManaClash is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.


