from team import team
from heroes import heroes
class match():
    def __init__(self):
        self.team1 = team()
        self.team2 = team()
        self.admin = 0
        self.unselectedHeroes = set()
        for hero in heroes:
            self.unselectedHeroes.add(hero)
        self.pickBanCount = 0


    def clearTeams(self):
        self.team1.players.clear()
        self.team2.players.clear()