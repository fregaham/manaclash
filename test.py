
from ManaClash import *

def test_common(g):
    g.create()

    c1 = []
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Hasty Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying",u"haste"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying"]), "", 1, 1))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Plains", None, set([u"basic"]), set([u"land"]), set(), set(), "[W]", None, None))
    c1.append (g.create_card (u"Hasty Suntail Hawk", "W", set(), set([u"creature"]), set([u"bird"]), set([u"flying",u"haste"]), "", 1, 1))

    p1 = g.create_player("Alice", c1)

    c2 = []
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Scatchy Zombies", "B", set(), set([u"creature"]), set([u"zombie"]), set([u"haste"]), "", 2, 2))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))
    c2.append (g.create_card (u"Swamp", None, set([u"basic"]), set([u"land"]), set(), set(), "[B]", None, None))

    p2 = g.create_player("Bob", c2)

    process_game(g)

    return (p1, p2)

def test1():
    ig = test_input_generator([0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    n = ig.next()
    g = Game(ig)
    test_common(g)

def test2():
    ig = test_input_generator([0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0,0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 1, 3,1, 2, 0, 0, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
    n = ig.next()
    g = Game(ig)
    alice, bob = test_common(g)    
    alice_graveyard = g.get_graveyard(alice)
    assert len(alice_graveyard.objects) == 2 
    assert alice_graveyard.objects[0].state.title == "Suntail Hawk"
    print alice_graveyard.objects[1].state.title
    assert alice_graveyard.objects[1].state.title == "Suntail Hawk"
    

if __name__ == "__main__":
    test1()
    test2()

