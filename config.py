import os

class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_TRACK_MODIFACTION = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", None)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql://{username}:{password}@{hostname}/{databasename}".format(
        username="root",
        password="root",
        hostname="localhost:3306",
        databasename="vgmanager"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", None)
    CACHE_TYPE = "null"
