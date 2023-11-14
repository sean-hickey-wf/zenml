"""fix external_input_artifacts [729263e47b55].

Revision ID: 729263e47b55
Revises: 0.45.2
Create Date: 2023-10-18 08:07:33.374613

"""
import json

from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "729263e47b55"
down_revision = "0.45.2"
branch_labels = None
depends_on = None

update_query_pd = text(
    "UPDATE pipeline_deployment SET step_configurations = :data WHERE id = :id_"
)

update_query_sr = text(
    "UPDATE step_run SET step_configuration = :data WHERE id = :id_"
)


def upgrade() -> None:
    """Upgrade database schema and/or data, creating a new revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = Session(bind=bind)
    # update pipeline_deployment
    rows_pd = session.execute(
        text(
            """
             SELECT id, step_configurations 
             FROM pipeline_deployment 
             WHERE step_configurations IS NOT NULL
             """
        )
    )
    for id_, data in rows_pd:
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError:
            continue
        has_changes = False
        for k in data_dict:
            if (
                "config" in data_dict[k]
                and "external_input_artifacts" in data_dict[k]["config"]
            ):
                for eip_name in data_dict[k]["config"][
                    "external_input_artifacts"
                ]:
                    current = data_dict[k]["config"][
                        "external_input_artifacts"
                    ][eip_name]
                    if not isinstance(current, dict):
                        data_dict[k]["config"]["external_input_artifacts"][
                            eip_name
                        ] = {"id": current}
                        has_changes = True
        if has_changes:
            data = json.dumps(data_dict)
            session.execute(update_query_pd, params=(dict(data=data, id_=id_)))

    # update step_run
    rows_sr = session.execute(
        text(
            """
             SELECT id, step_configuration 
             FROM step_run 
             WHERE step_configuration IS NOT NULL
             """
        )
    )
    for id_, data in rows_sr:
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError:
            continue
        has_changes = False
        if (
            "config" in data_dict
            and "external_input_artifacts" in data_dict["config"]
        ):
            for eip_name in data_dict["config"]["external_input_artifacts"]:
                current = data_dict["config"]["external_input_artifacts"][
                    eip_name
                ]
                if not isinstance(current, dict):
                    data_dict["config"]["external_input_artifacts"][
                        eip_name
                    ] = {"id": current}
                    has_changes = True
        if has_changes:
            data = json.dumps(data_dict)
            session.execute(update_query_sr, params=(dict(data=data, id_=id_)))
    session.commit()
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade database schema and/or data back to the previous revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = Session(bind=bind)
    # update pipeline_deployment
    rows = session.execute(
        text(
            """
             SELECT id,step_configurations 
             FROM pipeline_deployment 
             WHERE step_configurations IS NOT NULL
             """
        )
    )
    for id_, data in rows:
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError:
            continue
        for k in data_dict:
            has_changes = False
            if (
                "config" in data_dict[k]
                and "external_input_artifacts" in data_dict[k]["config"]
            ):
                for eip_name in data_dict[k]["config"][
                    "external_input_artifacts"
                ]:
                    current = data_dict[k]["config"][
                        "external_input_artifacts"
                    ][eip_name]
                    if isinstance(current, dict):
                        data_dict[k]["config"]["external_input_artifacts"][
                            eip_name
                        ] = current["id"]
                        has_changes = True
        if has_changes:
            data = json.dumps(data_dict)
            session.execute(update_query_pd, params=(dict(data=data, id_=id_)))

    # update step_run
    rows_sr = session.execute(
        text(
            """
             SELECT id, step_configuration 
             FROM step_run 
             WHERE step_configuration IS NOT NULL
             """
        )
    )
    for id_, data in rows_sr:
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError:
            continue
        has_changes = False
        if (
            "config" in data_dict
            and "external_input_artifacts" in data_dict["config"]
        ):
            for eip_name in data_dict["config"]["external_input_artifacts"]:
                current = data_dict["config"]["external_input_artifacts"][
                    eip_name
                ]
                if isinstance(current, dict):
                    data_dict["config"]["external_input_artifacts"][
                        eip_name
                    ] = current["id"]
                    has_changes = True
        if has_changes:
            data = json.dumps(data_dict)
            session.execute(update_query_sr, params=(dict(data=data, id_=id_)))

    session.commit()
    # ### end Alembic commands ###
