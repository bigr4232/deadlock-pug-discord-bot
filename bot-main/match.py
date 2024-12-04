from team import team
class match():
    def __init__(self):
        self.team1 = team()
        self.team2 = team()
        self.admin = 0

    def clearTeams(self):
        self.team1.players.clear()
        self.team2.players.clear()