from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from flask_app import db


class Elo(db.Model):
    __tablename__ = "elo"

    id = db.Column(db.String(128), primary_key=True)
    date = db.Column(db.DateTime)

    team_id = db.Column(db.String(128), db.ForeignKey("team.id"))
    guild_id = db.Column(db.String(128), db.ForeignKey("guild.id"))


class TeamChallenge(db.Model):
    __tablename__ = "team_challenge"

    id = db.Column(db.String(128), primary_key=True)
    team1_id = db.Column(db.String(128), db.ForeignKey("team.id"))
    team2_id = db.Column(db.String(128), db.ForeignKey("team.id"))

    mode = db.Column(db.String(128))
    start = db.Column(db.DateTime, default=func.now())
    end = db.Column(db.DateTime, default=func.now())

    status = db.Column(db.String(32))

    _team1 = db.relationship("Team", foreign_keys=[team1_id])
    _team2 = db.relationship("Team", foreign_keys=[team2_id])
    _matches = db.relationship("Roster", primaryjoin="or_(Roster.team_id==TeamChallenge.team1_id, Roster.team_id==TeamChallenge.team2_id)", foreign_keys="[Roster.team_id]")

class GuildChallenge(db.Model):
    __tablename__ = "guild_challenge"

    id = db.Column(db.String(128), primary_key=True)
    guild1_id = db.Column(db.String(128), db.ForeignKey("guild.id"))
    guild2_id = db.Column(db.String(128), db.ForeignKey("guild.id"))

    mode = db.Column(db.String(128))
    start = db.Column(db.DateTime, default=func.now())
    end = db.Column(db.DateTime, default=func.now())

    _guild1 = db.relationship("Guild", foreign_keys=[guild1_id])
    _guild2 = db.relationship("Guild", foreign_keys=[guild2_id])
    _matches = db.relationship("Roster", primaryjoin="or_(Roster.guild_id==GuildChallenge.guild1_id, Roster.guild_id==GuildChallenge.guild2_id)", foreign_keys="[Roster.guild_id]")


class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.String(128), primary_key=True)
    captain = db.Column(db.String(128), db.ForeignKey("player.id"))
    officer = db.Column(db.String(128), db.ForeignKey("player.id"))

    name = db.Column(db.String(128))
    tag = db.Column(db.String(128))
    description = db.Column(db.String(128))
    shardId = db.Column(db.String(128))

    _captain = db.relationship("Player", backref="team_captain", uselist=False, primaryjoin="Team.captain==Player.id", foreign_keys="[Player.id]")
    _officer = db.relationship("Player", backref="team_officer", uselist=False, primaryjoin="Team.officer==Player.id", foreign_keys="[Player.id]")

    _members = db.relationship("Player", backref="team", primaryjoin="Team.id==Player.team_id", foreign_keys="[Player.team_id]")
    _matches = db.relationship("Roster", primaryjoin="Roster.team_id==Team.id", foreign_keys="[Roster.team_id]")
    _challenges = db.relationship("TeamChallenge", primaryjoin="or_(TeamChallenge.team1_id==Team.id, TeamChallenge.team2_id==Team.id)")
    _elo = db.relationship("Elo", backref="team")

    @hybrid_property
    def skillTier(self):
        skilltiers = [m.skillTier for m in self._members]
        try:
            return sum(skilltiers) / len(skilltiers)
        except ZeroDivisionError:
            return -1

    @hybrid_property
    def winrate(self):
        won = [m.winner for m in self._matches]
        try:
            return (sum(won) / float(len(won))) * 100
        except ZeroDivisionError:
            return 0

    @hybrid_property
    def duration(self):
        durations = [m.match.duration for m in self._matches]
        try:
            return sum(durations) / float(len(durations))
        except ZeroDivisionError:
            return 0

    def __init__(self, **kwargs):
        super(Team, self).__init__(**kwargs)

    def __repr__(self):
        return self.name


class Guild(db.Model):
    __tablename__ = "guild"

    id = db.Column(db.String(128), primary_key=True)
    captain = db.Column(db.String(128), db.ForeignKey("player.id"))
    officer = db.Column(db.String(128), db.ForeignKey("player.id"))

    name = db.Column(db.String(128))
    tag = db.Column(db.String(128))
    description = db.Column(db.String(128))
    shardId = db.Column(db.String(128))

    _captain = db.relationship("Player", backref="guild_captain", uselist=False, primaryjoin="Guild.captain==Player.id", foreign_keys="[Player.id]")
    _officer = db.relationship("Player", backref="guild_officer", uselist=False, primaryjoin="Guild.officer==Player.id", foreign_keys="[Player.id]")

    _members = db.relationship("Player", backref="guild", primaryjoin="Guild.id==Player.guild_id", foreign_keys="[Player.guild_id]")
    _matches = db.relationship("Roster", primaryjoin="Roster.guild_id==Guild.id", foreign_keys="[Roster.guild_id]")
    _challenges = db.relationship("GuildChallenge", primaryjoin="or_(GuildChallenge.guild1_id==Guild.id, GuildChallenge.guild2_id==Guild.id)")
    _elo = db.relationship("Elo", backref="guild")

    @hybrid_property
    def skillTier(self):
        skilltiers = [m.skillTier for m in self._members]
        try:
            return sum(skilltiers) / len(skilltiers)
        except ZeroDivisionError:
            return -1

    @hybrid_property
    def winrate(self):
        won = [m.winner for m in self._matches]
        try:
            return (sum(won) / float(len(won))) * 100
        except ZeroDivisionError:
            return 0

    @hybrid_property
    def duration(self):
        durations = [m.match.duration for m in self._matches]
        try:
            return sum(durations) / float(len(durations))
        except ZeroDivisionError:
            return 0

    def __init__(self, **kwargs):
        super(Guild, self).__init__(**kwargs)

    def __repr__(self):
        return self.name


class Match(db.Model):
    __tablename__ = "match"

    id = db.Column(db.String(128), primary_key=True)
    createdAt = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    gameMode = db.Column(db.String(128))
    shardId = db.Column(db.String(128))
    patchVersion = db.Column(db.String(128))
    endGameReason = db.Column(db.String(128))
    queue = db.Column(db.String(128))

    rosters = db.relationship("Roster", backref="match")

    @hybrid_property
    def left(self):
        for roster in self.rosters:
            if roster.side == "left/blue":
                return roster

    @hybrid_property
    def right(self):
        for roster in self.rosters:
            if roster.side == "right/red":
                return roster

    def __init__(self, **kwargs):
        super(Match, self).__init__(**kwargs)


class Roster(db.Model):
    __tablename__ = "roster"

    id = db.Column(db.String(128), primary_key=True)
    match_id = db.Column(db.String(128), db.ForeignKey("match.id"))
    team_id = db.Column(db.String(128))
    guild_id = db.Column(db.String(128))

    acesEarned = db.Column(db.Integer)
    gold = db.Column(db.Integer)
    heroKills = db.Column(db.Integer)
    krakenCaptures = db.Column(db.Integer)
    side = db.Column(db.String(128))
    turrentKills = db.Column(db.Integer)
    turrentsRemaining = db.Column(db.Integer)
    team_api = db.Column(db.String(128))

    participants = db.relationship("Participant", backref="roster")

    _team = db.relationship("Team", backref="roster", uselist=False, primaryjoin="Roster.team_id==Team.id", foreign_keys="[Team.id]")
    _guild = db.relationship("Guild", backref="roster", uselist=False, primaryjoin="Roster.guild_id==Guild.id", foreign_keys="[Guild.id]")

    @hybrid_property
    def winner(self):
        return self.participants[0].winner

    @hybrid_property
    def heroes(self):
        return [(p.actor, p.player) for p in self.participants]

    def __init__(self, **kwargs):
        super(Roster, self).__init__(**kwargs)


class Participant(db.Model):
    __tablename__ = "participant"

    id = db.Column(db.String(128), primary_key=True)
    player_id = db.Column(db.String(128), db.ForeignKey("player.id"))
    roster_id = db.Column(db.String(128), db.ForeignKey("roster.id"))

    actor = db.Column(db.String(128))
    kills = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    crystalMineCaptures = db.Column(db.Integer)
    goldMindCaptures = db.Column(db.Integer)
    krakenCaptures = db.Column(db.Integer)
    turrentCaptures = db.Column(db.Integer)

    winner = db.Column(db.Boolean)

    farm = db.Column(db.Integer)
    minionKills = db.Column(db.Integer)
    nonJungleMinionKills = db.Column(db.Integer)
    jungleKills = db.Column(db.Integer)

    firstAfkTime = db.Column(db.Integer)
    wentAfk = db.Column(db.Boolean)
    itemGrants = db.Column(db.PickleType)
    itemSells = db.Column(db.PickleType)
    itemUses = db.Column(db.PickleType)
    items = db.Column(db.PickleType)

    skinKey = db.Column(db.String(128))
    karmaLevel = db.Column(db.Integer)
    level = db.Column(db.Integer)
    skillTier = db.Column(db.Integer)

    createdAt = db.Column(db.DateTime, default=func.now())

    def __init__(self, **kwargs):
        super(Participant, self).__init__(**kwargs)


class Player(db.Model):
    __tablename__ = "player"

    id = db.Column(db.String(128), primary_key=True)
    team_id = db.Column(db.String(128), db.ForeignKey("team.id"))
    guild_id = db.Column(db.String(128), db.ForeignKey("guild.id"))

    shardId = db.Column(db.String(128))
    name = db.Column(db.String(128))
    lifetimeGold = db.Column(db.Integer)
    lossStreak = db.Column(db.Integer)
    winStreak = db.Column(db.Integer)
    played = db.Column(db.Integer)
    played_ranked = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    xp = db.Column(db.Integer)

    participated = db.relationship("Participant", backref="player", order_by="desc(Participant.createdAt)")

    @hybrid_property
    def skillTier(self):
        if self.participated:
            return self.participated[0].skillTier
        else:
            return -1

    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)

    def __repr__(self):
        return self.name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
