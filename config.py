class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_TRACK_MODIFACTION = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgres://poofkjsspeyigb:2ba845148050fd1119d928e40178d69b0e7a627d1ee5d26f2219d42416362df1@ec2-54-228-235-185.eu-west-1.compute.amazonaws.com:5432/d9vilu9trlu64l"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql://{username}:{password}@{hostname}/{databasename}".format(
        username="root",
        password="root",
        hostname="localhost:3306",
        databasename="vgmanager"
    )
    CACHE_TYPE = "null"
