"""empty message

Revision ID: ab7ea8b4ea7b
Revises: e2e7563201a7
Create Date: 2017-05-03 19:02:40.531000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab7ea8b4ea7b'
down_revision = 'e2e7563201a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('team_challenge', sa.Column('category', sa.String(length=128), nullable=True))
    op.add_column('team_challenge', sa.Column('end', sa.DateTime(), nullable=True))
    op.add_column('team_challenge', sa.Column('start', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('team_challenge', 'start')
    op.drop_column('team_challenge', 'end')
    op.drop_column('team_challenge', 'category')
    # ### end Alembic commands ###