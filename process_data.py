import datetime

from sqlalchemy.exc import SQLAlchemyError

from flask_app import app, db
from models import Team, Guild, Match, Roster, Participant, Player


def process_batch_query(matches):
    teams = db.session.query(Team).all()
    teams = [(team.id, {member.id for member in team._members}) for team in teams]
    guilds = db.session.query(Guild).all()
    guilds = [(guild.id, {member.id for member in guild._members}) for guild in guilds]

    for match in matches['data']:
        team_roster = {}
        guild_roster = {}
        for roster in match['relationships']['rosters']['data']:
            roster_data = [i for i in matches['included'] if i['id'] == roster['id']]
            participants = set()
            for participant in roster_data[0]['relationships']['participants']['data']:
                participant_data = [i['relationships']['player']['data']['id'] for i in matches['included'] if
                                    i['id'] == participant['id']]
                participants.add(participant_data[0])

            for team_id, members in teams:
                if participants < members:
                    team_roster[roster['id']] = team_id
            for guild_id, members in guilds:
                if participants < members:
                    guild_roster[roster['id']] = guild_id

        if team_roster or guild_roster:
            process_match(match)
            createdAt = datetime.datetime.strptime(match['attributes']['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
            shardId = match['attributes']['shardId']

            for roster in match['relationships']['rosters']['data']:
                roster_data = [i for i in matches['included'] if i['id'] == roster['id']]
                assert len(roster_data) == 1

                team_id = None
                guild_id = None
                if roster['id'] in team_roster:
                    team_id = team_roster[roster['id']]
                if roster['id'] in guild_roster:
                    guild_id = guild_roster[roster['id']]

                process_roster(roster_data[0], match['id'], team_id=team_id, guild_id=guild_id)

                for participant in roster_data[0]['relationships']['participants']['data']:
                    participant_data = [i for i in matches['included'] if i['id'] == participant['id']]
                    assert len(participant_data) == 1

                    player_data = [i for i in matches['included'] if
                                   i['id'] == participant_data[0]['relationships']['player']['data']['id']]
                    assert len(player_data) == 1
                    process_player(player_data[0], region=shardId)
                    process_participant(participant_data[0], roster['id'], createdAt=createdAt)


def process_match(data):
    test = db.session.query(Match).get(data['id'])
    if not test:
        m = Match(id=data['id'],
                  createdAt=datetime.datetime.strptime(data['attributes']['createdAt'], '%Y-%m-%dT%H:%M:%SZ'),
                  duration=data['attributes']['duration'],
                  gameMode=data['attributes']['gameMode'],
                  patchVersion=data['attributes']['patchVersion'],
                  shardId=data['attributes']['shardId'],
                  endGameReason=data['attributes']['stats']['endGameReason'],
                  queue=data['attributes']['stats']['queue'])

        db.session.add(m)

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))


def process_roster(data, match_id, team_id=None, guild_id=None):
    test = db.session.query(Roster).get(data['id'])
    if not test:
        r = Roster(id=data['id'], match_id=match_id,
                   acesEarned=data['attributes']['stats']['acesEarned'],
                   gold=data['attributes']['stats']['gold'],
                   heroKills=data['attributes']['stats']['heroKills'],
                   krakenCaptures=data['attributes']['stats']['krakenCaptures'],
                   side=data['attributes']['stats']['side'],
                   turrentKills=data['attributes']['stats']['turretKills'],
                   turrentsRemaining=data['attributes']['stats']['turretsRemaining'],
                   team_api=data['relationships']['team']['data'])
        if team_id:
            r.team_id = team_id
        if guild_id:
            r.guild_id = guild_id

        db.session.add(r)

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))


def process_participant(data, roster_id, createdAt=None):
    test = db.session.query(Participant).get(data['id'])
    if not test:
        p = Participant(id=data['id'], roster_id=roster_id,
                        player_id=data['relationships']['player']['data']['id'],
                        actor=data['attributes']['actor'],
                        kills=data['attributes']['stats']['kills'],
                        assists=data['attributes']['stats']['assists'],
                        deaths=data['attributes']['stats']['deaths'],
                        jungleKills=data['attributes']['stats']['jungleKills'],
                        crystalMineCaptures=data['attributes']['stats']['crystalMineCaptures'],
                        goldMindCaptures=data['attributes']['stats']['goldMineCaptures'],
                        krakenCaptures=data['attributes']['stats']['krakenCaptures'],
                        turrentCaptures=data['attributes']['stats']['turretCaptures'],
                        winner=data['attributes']['stats']['winner'],
                        farm=data['attributes']['stats']['farm'],
                        minionKills=data['attributes']['stats']['minionKills'],
                        nonJungleMinionKills=data['attributes']['stats']['nonJungleMinionKills'],
                        firstAfkTime=data['attributes']['stats']['firstAfkTime'],
                        wentAfk=data['attributes']['stats']['wentAfk'],
                        itemGrants=data['attributes']['stats']['itemGrants'],
                        itemSells=data['attributes']['stats']['itemSells'],
                        itemUses=data['attributes']['stats']['itemUses'],
                        items=data['attributes']['stats']['items'],
                        skinKey=data['attributes']['stats']['skinKey'],
                        karmaLevel=data['attributes']['stats']['karmaLevel'],
                        level=data['attributes']['stats']['level'],
                        skillTier=data['attributes']['stats']['skillTier'])
        if createdAt:
            p.createdAt = createdAt
        db.session.add(p)

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))


def process_player(data, region="eu"):
    test = db.session.query(Player).get(data['id'])
    if not test:

        p = Player(id=data['id'], name=data['attributes']['name'],
                   shardId=region,
                   lifetimeGold=data['attributes']['stats']['lifetimeGold'],
                   lossStreak=data['attributes']['stats']['lossStreak'],
                   winStreak=data['attributes']['stats']['winStreak'],
                   played=data['attributes']['stats']['played'],
                   played_ranked=data['attributes']['stats']['played_ranked'],
                   wins=data['attributes']['stats']['wins'],
                   xp=data['attributes']['stats']['xp'])

        db.session.add(p)

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
    else:
        test.lifetimeGold = data['attributes']['stats']['lifetimeGold']
        test.lossStreak = data['attributes']['stats']['lossStreak']
        test.winStreak = data['attributes']['stats']['winStreak']
        test.played = data['attributes']['stats']['played']
        test.played_ranked = data['attributes']['stats']['played_ranked']
        test.wins = data['attributes']['stats']['wins']
        test.xp = data['attributes']['stats']['xp']

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
