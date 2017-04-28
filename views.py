import time
import uuid
from functools import wraps

from flask import render_template, abort, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from requests import HTTPError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import load_only

import process_data
import request_data
from flask_app import app, db, login_manager
from models import Player, Team, Guild, Match
import commons


@login_manager.user_loader
def load_user(id):
    return Player.query.get(id)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
@app.route('/index/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    else:
        return render_template('login.html')


@app.route('/signup/', methods=['GET'])
def subscribe():
    return render_template('signup.html')


@app.route('/ajax_signup/', methods=['POST'])
def ajax_subscribe():
    error = []

    type = request.form['subscribe-form-type']
    name = request.form['subscribe-form-name']
    tag = request.form['subscribe-form-tag']
    description = request.form['subscribe-form-description']
    region = request.form['subscribe-form-region']
    print(type, name, tag, region)

    if len(name) < 2 or len(name) > 16:
        error.append('Invalid name')

    if len(tag) < 2 or len(tag) > 4:
        error.append('Invalid region')

    if not error:
        if type == 'team':
            team = Team(id=uuid.uuid4(), name=name, tag=tag, shardId=region, description=description)
        else:
            team = Guild(id=uuid.uuid4(), name=name, tag=tag, shardId=region, description=description)

        try:
            db.session.add(team)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))

    return jsonify({'error': ', '.join(error)})


@app.route('/ajax_join_group/', methods=['POST'])
def ajax_join_group():
    error = []

    type = request.form['subscribe-form-type']
    name = request.form['subscribe-form-name']

    user = db.session.query(Player).get(current_user.id)
    if type == 'team':
        team = db.session.query(Team).filter_by(name=name).one()
        user.team_id = team.id
    else:
        guild = db.session.query(Guild).filter_by(name=name).one()
        user.guild_id = guild.id

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))

    return jsonify({'error': ', '.join(error)})


@app.route('/profile/', methods=['GET'])
@login_required
def profile():
    player = db.session.query(Player).get(current_user.id)
    guilds = db.session.query(Guild).options(load_only("name")).all()
    teams = db.session.query(Team).options(load_only("name")).all()
    return render_template('profile.html', player=player, teams=teams, guilds=guilds)


@app.route('/profile/<string:player_id>/', methods=['GET'])
def public_profile(player_id):
    player = db.session.query(Player).get(player_id)
    team = None
    guild = None
    if player.team_id:
        team = db.session.query(Team).get(player.team_id)
    if player.guild_id:
        guild = db.session.query(Guild).get(player.guild_id)
    return render_template('player.html', player=player, guild=guild, team=team)


@app.route('/ajax_update_player/', methods=['POST'])
@login_required
def ajax_update_player():
    player_id = request.form['player_id']
    player = db.session.query(Player).get(player_id)

    if not player:
        abort(404)

    # print("-- Start casual")
    # result = request_data.process_id(player_id, "casual")
    # process_data.process_batch_query(result)
    # print("-- Finished casual")

    print("-- Start ranked")
    result = request_data.process_id(player_id, "ranked")
    process_data.process_batch_query(result)
    print("-- Finished ranked")
    return jsonify({'status': 200})


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        name = request.form['login-form-username']
        region = request.form['login-form-region']
        remember_me = 'remember' in request.form

        registered_user = Player.query.filter_by(name=name).first()
        if registered_user is None:
            try:
                player = request_data.query_player(name, region)
            except (request_data.PlayerNotFound, HTTPError) as e:
                flash(e.message)
                return redirect(url_for('login'))

            add_player = Player(id=player['id'], name=player['attributes']['name'],
                                shardId=region,
                                lifetimeGold=player['attributes']['stats']['lifetimeGold'],
                                lossStreak=player['attributes']['stats']['lossStreak'],
                                winStreak=player['attributes']['stats']['winStreak'],
                                played=player['attributes']['stats']['played'],
                                played_ranked=player['attributes']['stats']['played_ranked'],
                                wins=player['attributes']['stats']['wins'],
                                xp=player['attributes']['stats']['xp'])

            try:
                db.session.add(add_player)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
                flash("Something went wrong, please try again later.")
                return redirect(url_for('login'))

            registered_user = Player.query.filter_by(name=name).first()

        login_user(registered_user, remember=remember_me)
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout/')
def logout():
    logout_user()
    return render_template('login.html')


@app.route('/teams/')
def teams():
    teams = db.session.query(Team).all()
    return render_template('teams.html', teams=teams, active="team")


@app.route('/team/<string:team_id>/')
def team(team_id):
    team = db.session.query(Team).get(team_id)
    if not team:
        abort(404)

    return render_template('team.html', team=team, active="team")


@app.route('/guild/<string:guild_id>/')
def guild(guild_id):
    guild = db.session.query(Guild).get(guild_id)
    if not guild:
        abort(404)
    return render_template('team.html', team=guild, active="guild")


@app.route('/guilds/')
def guilds():
    guilds = db.session.query(Guild).all()
    return render_template('guilds.html', guilds=guilds, active="guild")


@app.route('/match/<string:match_id>/')
def match(match_id):
    match = db.session.query(Match).get(match_id)
    if not match:
        abort(404)
    return render_template('match.html', match=match)


@app.route('/debug/')
def test():
    # teams = db.session.query(Team).all()
    # player_ids = [member.id for team in teams for member in team._members]
    # chunks = [player_ids[x:x + 10] for x in range(0, len(player_ids), 10)]
    # for chunk in chunks:
    #     request_data.threaded_process_range(2, chunk, gamemode)
    #     print("time.sleep(60)")
    #     time.sleep(60)

    # request_data.query_team("cca544dd-8fb9-4640-97fa-d20aee017639")

    team = db.session.query(Team).filter_by(tag="FT").one()
    db.session.delete(team)

    print("Query #1 " + time.strftime("%Y-%m-%dT%H:%M%SZ"))
    player = request_data.query_player("Nyria", "eu")
    add_player = Player(id=player['id'], name=player['attributes']['name'], shardId="eu",
                        lifetimeGold=player['attributes']['stats']['lifetimeGold'],
                        lossStreak=player['attributes']['stats']['lossStreak'],
                        winStreak=player['attributes']['stats']['winStreak'],
                        played=player['attributes']['stats']['played'],
                        played_ranked=player['attributes']['stats']['played_ranked'],
                        wins=player['attributes']['stats']['wins'],
                        xp=player['attributes']['stats']['xp'])
    try:
        db.session.add(add_player)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))

    # guild_id = db.session.query(Guild).filter_by(tag="FT").one()
    # guild =  ["DaZac", "Nyria", "MarcoNewgate", "sugab", "farizhakim", "Kootiz", "Conchobhar", "XardaS",
    #           "XSM1X", "WestSideTK", "R3zA", "krelian", "iTsKerim", "standart", "loyalkiller", "StormNeos", "time2party",
    #           "salkoamok", "KanonMara", "GeTR3kT1337", "snowGhost", "TheBigBadWolf95", "shanlom", "MaestroTg",
    #           "insomniax", "moaner", "Shiqan", "Madara420", "Globalkiller", "iNach", "yMadbro", "KaDJin", "SkullTune",
    #           "CoOperPL", "TheWongDecision"]
    # for member in guild:
    #     player = db.session.query(Player).filter_by(name=member).first()
    #     if player:
    #         player.guild_id = guild_id.id
    #         try:
    #             db.session.commit()
    #         except SQLAlchemyError as e:
    #             db.session.rollback()
    #             app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
    # teams = [("Gauntlet","jdmn", ["loyalkiller", "snowGhost", "7DAD", "Ferxya", "moaner", "Lino95"]),
    # ("TheBloodLine", "wBL",["KaDJin","leadena","BIAHOS","Setouph","Salamankka"]),
    # ("partyharder","pH",["krelian","salkoamok","Conchobhar"]),
    # ("Ash Beast","AshB",["DaZac","Madara420","CALLMEJESUS","GeTR3kT1337","TheWongDecision"]),
    # ("Ja Gege","JGG",["sugab","farizhakim","R3zA"]),
    # ("Bigby Wolf","BBW",["TheBigBadWolf95","MubarakWaleed","Globalkiller","VaLaK11","LightningCloud"]),
    # ("NOO Regrets","NR",["ibrahimali12","KristinaEU","WestWorLd","insomniax","Girl83"]),
    # ("Wanted Sultans", "WaSu", ["iUzername","WestSideTK","iTsKerim"]),
    # ("WTW","TBT",["Kirushu","MrPoulet75","Hermes75","Firows"]),
    # ("SickCr3w","Cr3w",["llEdokll","XSM1X","MarcoNewgate","Kootiz"]),
    # ("Collossoss","SOS",["Zagataga","llsorall","shockwave09"]),
    # ("InfernumOcularis","inoc",["standart","StormNeos","muroon"])]
    #
    # for team in teams:
    #     test = db.session.query(Team).filter_by(name=team[0]).first()
    #     if not test:
    #         test = Team(id=uuid.uuid4(), name=team[0], tag=team[1], shardId="eu")
    #
    #         try:
    #             db.session.add(test)
    #             db.session.commit()
    #         except SQLAlchemyError as e:
    #             db.session.rollback()
    #             app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
    #
    #     for member in team[2]:
    #         player = db.session.query(Player).filter_by(name=member).first()
    #         if not player:
    #             try:
    #                 player = request_data.query_player(member, "eu")
    #             except (request_data.PlayerNotFound, HTTPError) as e:
    #                 print(e)
    #                 continue
    #             add_player = Player(id=player['id'], name=player['attributes']['name'],
    #                                 shardId="eu",
    #                                 lifetimeGold=player['attributes']['stats']['lifetimeGold'],
    #                                 lossStreak=player['attributes']['stats']['lossStreak'],
    #                                 winStreak=player['attributes']['stats']['winStreak'],
    #                                 played=player['attributes']['stats']['played'],
    #                                 played_ranked=player['attributes']['stats']['played_ranked'],
    #                                 wins=player['attributes']['stats']['wins'],
    #                                 xp=player['attributes']['stats']['xp'])
    #             add_player.team_id = test.id
    #
    #             try:
    #                 db.session.add(add_player)
    #                 db.session.commit()
    #             except SQLAlchemyError as e:
    #                 db.session.rollback()
    #                 app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
    #         else:
    #             player.team_id = test.id
    #
    #             try:
    #                 db.session.commit()
    #             except SQLAlchemyError as e:
    #                 db.session.rollback()
    #                 app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))
    #     time.sleep(60)
    return 'ok'


# ------------------
# ERROR HANDLERS
# ------------------
@app.errorhandler(400)
def bad_request(e):
    return render_template('404.html'), 400


@app.errorhandler(401)
def not_authorized(e):
    return render_template('404.html'), 401


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('404.html'), 405


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500
