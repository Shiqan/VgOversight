import datetime
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
from models import Player, Team, Guild, Match, TeamChallenge, GuildChallenge
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

            process_data.process_player(player, region=region)
            registered_user = Player.query.filter_by(name=name).first()
            if registered_user is None:
                return redirect(url_for('login'))

        login_user(registered_user, remember=remember_me)
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout/')
def logout():
    logout_user()
    return render_template('login.html')


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
        error.append('Invalid tag')

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


@app.route('/teams/')
def teams():
    teams = db.session.query(Team).all()
    return render_template('teams.html', teams=teams, title="Teams", active="team")


@app.route('/team/<string:team_id>/')
def team(team_id):
    teams = db.session.query(Team).filter(Team.id != team_id).all()
    team = db.session.query(Team).get(team_id)
    if not team:
        abort(404)

    return render_template('team.html', team=team, teams=teams, active="team")


@app.route('/guild/<string:guild_id>/')
def guild(guild_id):
    guilds = db.session.query(Guild).filter(Guild.id != guild_id).all()
    guild = db.session.query(Guild).get(guild_id)
    if not guild:
        abort(404)
    return render_template('team.html', team=guild, teams=guilds, active="guild")


@app.route('/guilds/')
def guilds():
    guilds = db.session.query(Guild).all()
    return render_template('teams.html', teams=guilds, title="Guilds", active="guild")


@app.route('/ajax_challenge/', methods=['POST'])
def ajax_challenge():
    error = []

    type = request.form['challenge-form-type']
    challenger = uuid.UUID(request.form['challenge-form-current'])
    challenged = request.form['challenge-form-name']
    mode = request.form['challenge-form-mode']

    start_date = datetime.datetime.now()
    end_date = start_date + datetime.timedelta(days=7)

    if type == 'team':
        team1 = db.session.query(Team).filter_by(id=challenger).one()
        team2 = db.session.query(Team).filter_by(name=challenged).one()

        challenge = TeamChallenge(id=uuid.uuid4(), team1_id=team1.id, team2_id=team2.id, start=start_date, end=end_date, mode=mode)
    else:
        guild1 = db.session.query(Guild).filter_by(id=challenger).one()
        guild2 = db.session.query(Guild).filter_by(name=challenged).one()

        challenge = GuildChallenge(id=uuid.uuid4(), guild1_id=guild1.id, guild2_id=guild2.id, start=start_date, end=end_date, mode=mode)

    try:
        db.session.add(challenge)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error('ERROR: Session rollback - reason "%s"' % str(e))

    return jsonify({'error': ', '.join(error)})


@app.route('/match/<string:match_id>/')
def match(match_id):
    match = db.session.query(Match).get(match_id)
    if not match:
        abort(404)
    return render_template('match.html', match=match)


@app.route('/debug/')
def test():
    teams = db.session.query(Team).all()
    player_ids = [member.id for team in teams for member in team._members]
    chunks = [player_ids[x:x + 10] for x in range(0, len(player_ids), 10)]
    for chunk in chunks:
        request_data.threaded_process_range(2, chunk, "ranked")
        print("time.sleep(60)")
        time.sleep(60)
          
    return 'ok'


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
