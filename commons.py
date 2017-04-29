import strings
from flask_app import app, db
from models import Team, Guild


@app.template_filter('convert_game_time')
def seconds_to_minutes(time):
    m, s = divmod(time, 60)
    m = int(round(m))
    s = int(round(s))
    if s < 10:
        s = "0" + str(s)
    return "{0}:{1}".format(m, s)


@app.template_filter('convert_hero_name')
def id_to_hero(id):
    return strings.heroes[id]


@app.template_filter('hero_to_img')
def hero_to_img(id):
    return "{0}.png".format(strings.heroes[id].lower())


@app.template_filter('item_to_img')
def item_to_img(item):
    return "{0}.png".format(item.lower().replace(" ", "-").replace('\'', ''))


@app.template_filter('convert_team_id')
def id_to_team(id):
    return db.session.query(Team).get(id)


@app.template_filter('convert_guild_id')
def id_to_guild(id):
    return db.session.query(Guild).get(id)
