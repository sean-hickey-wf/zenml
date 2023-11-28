"""Add pipeline run unique constraint [6917bce75069].

Revision ID: 6917bce75069
Revises: 0.50.0
Create Date: 2023-11-15 16:07:24.343126

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6917bce75069"
down_revision = "0.50.0"
branch_labels = None
depends_on = None


def add_orchestrator_run_id_for_old_runs() -> None:
    """Add orchestrator_run_id for old runs.

    In order to add the unique constraint on deployment_id and
    orchestrator_run_id, we first need to make sure all existing runs fulfill
    this constraint. This is not the case for old pipeline runs which existed
    before we had deployments, so we add a dummy value for those runs.
    """
    meta = sa.MetaData(bind=op.get_bind())
    meta.reflect(only=("pipeline_run",))
    run_table = sa.Table("pipeline_run", meta)
    connection = op.get_bind()

    query = (
        sa.update(run_table)
        .where(run_table.c.deployment_id.is_(None))
        .where(run_table.c.orchestrator_run_id.is_(None))
        .values(
            orchestrator_run_id="dummy_"
            + sa.func.cast(run_table.c.id, sa.types.Text)
        )
    )
    connection.execute(query)


def verify_unique_constraint_satisfied() -> None:
    """Verifies that the unique constraint will be satisfied.

    Raises:
        RuntimeError: If there are rows which have identical values for the
            `deployment_id` and `orchestrator_run_id` columns.
    """
    meta = sa.MetaData(bind=op.get_bind())
    meta.reflect(only=("pipeline_run",))
    run_table = sa.Table("pipeline_run", meta)
    connection = op.get_bind()

    query = (
        sa.select(run_table.c.deployment_id, run_table.c.orchestrator_run_id)
        .group_by(run_table.c.deployment_id, run_table.c.orchestrator_run_id)
        .having(sa.func.count() > 1)
    )
    result = connection.execute(query).fetchall()

    if result:
        raise RuntimeError(
            "Unable to migrate database because the `pipeline_run` table "
            "contains rows with identical values for both the "
            "`orchestrator_run_id` and the `deployment_id` columns."
        )


def upgrade() -> None:
    """Upgrade database schema and/or data, creating a new revision."""
    add_orchestrator_run_id_for_old_runs()
    verify_unique_constraint_satisfied()

    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("pipeline_run", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_orchestrator_run_id_for_deployment_id",
            ["deployment_id", "orchestrator_run_id"],
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade database schema and/or data back to the previous revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("pipeline_run", schema=None) as batch_op:
        batch_op.drop_constraint(
            "unique_orchestrator_run_id_for_deployment_id", type_="unique"
        )

    # ### end Alembic commands ###
