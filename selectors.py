
class Selector:
    def all (self):
        return []

class AllSelector:
    def all(self, game):
        for item in game.objects.values():
            yield item

class AllTypeSelector:
    def __init__ (self, type):
        self.type = type

    def all (self, game):
        for item in game.objects.values():
            if self.type in item.state.types:
                yield item

class AllPermanentSelector:
    def all(self, game):
         for item in game.objects.values():
            if "permanent" in item.state.tags:
                yield item


class PermanentPlayerControlsSelector(Selector):
    def __init__ (self, player):
        self.player_id = player.id

    def all (self, game):
        for item in game.objects.values():
            if "permanent" in item.state.tags:
                if item.state.controller_id == self.player_id:
                    yield item


