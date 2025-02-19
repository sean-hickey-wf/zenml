#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""SQLModel implementation of artifact table."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship

from zenml.config.source import Source
from zenml.enums import (
    ArtifactType,
    ExecutionStatus,
    MetadataResourceTypes,
    TaggableResourceTypes,
)
from zenml.models import (
    ArtifactResponse,
    ArtifactResponseBody,
    ArtifactResponseMetadata,
    ArtifactUpdate,
    ArtifactVersionRequest,
    ArtifactVersionResponse,
    ArtifactVersionResponseBody,
    ArtifactVersionResponseMetadata,
    ArtifactVersionUpdate,
)
from zenml.models.v2.core.artifact import ArtifactRequest
from zenml.zen_stores.schemas.base_schemas import BaseSchema, NamedSchema
from zenml.zen_stores.schemas.component_schemas import StackComponentSchema
from zenml.zen_stores.schemas.schema_utils import build_foreign_key_field
from zenml.zen_stores.schemas.step_run_schemas import (
    StepRunInputArtifactSchema,
    StepRunOutputArtifactSchema,
)
from zenml.zen_stores.schemas.user_schemas import UserSchema
from zenml.zen_stores.schemas.workspace_schemas import WorkspaceSchema

if TYPE_CHECKING:
    from zenml.zen_stores.schemas.artifact_visualization_schemas import (
        ArtifactVisualizationSchema,
    )
    from zenml.zen_stores.schemas.model_schemas import (
        ModelVersionArtifactSchema,
    )
    from zenml.zen_stores.schemas.run_metadata_schemas import RunMetadataSchema
    from zenml.zen_stores.schemas.tag_schemas import TagResourceSchema


class ArtifactSchema(NamedSchema, table=True):
    """SQL Model for artifacts."""

    __tablename__ = "artifact"

    # Fields
    has_custom_name: bool
    versions: List["ArtifactVersionSchema"] = Relationship(
        back_populates="artifact",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    tags: List["TagResourceSchema"] = Relationship(
        back_populates="artifact",
        sa_relationship_kwargs=dict(
            primaryjoin=f"and_(TagResourceSchema.resource_type=='{TaggableResourceTypes.ARTIFACT.value}', foreign(TagResourceSchema.resource_id)==ArtifactSchema.id)",
            cascade="delete",
            overlaps="tags",
        ),
    )

    @classmethod
    def from_request(
        cls,
        artifact_request: ArtifactRequest,
    ) -> "ArtifactSchema":
        """Convert an `ArtifactRequest` to an `ArtifactSchema`.

        Args:
            artifact_request: The request model to convert.

        Returns:
            The converted schema.
        """
        return cls(
            name=artifact_request.name,
            has_custom_name=artifact_request.has_custom_name,
        )

    def to_model(self, hydrate: bool = False) -> ArtifactResponse:
        """Convert an `ArtifactSchema` to an `ArtifactResponse`.

        Args:
            hydrate: bool to decide whether to return a hydrated version of the
                model.

        Returns:
            The created `ArtifactResponse`.
        """
        # Create the body of the model
        body = ArtifactResponseBody(
            created=self.created,
            updated=self.updated,
        )

        # Create the metadata of the model
        metadata = None
        if hydrate:
            metadata = ArtifactResponseMetadata(
                has_custom_name=self.has_custom_name,
                tags=[t.tag.to_model() for t in self.tags],
            )

        return ArtifactResponse(
            id=self.id,
            name=self.name,
            body=body,
            metadata=metadata,
        )

    def update(self, artifact_update: ArtifactUpdate) -> "ArtifactSchema":
        """Update an `ArtifactSchema` with an `ArtifactUpdate`.

        Args:
            artifact_update: The update model to apply.

        Returns:
            The updated `ArtifactSchema`.
        """
        self.updated = datetime.utcnow()
        if artifact_update.name:
            self.name = artifact_update.name
            self.has_custom_name = True
        return self


class ArtifactVersionSchema(BaseSchema, table=True):
    """SQL Model for artifact versions."""

    __tablename__ = "artifact_version"

    # Fields
    version: str
    version_number: Optional[int]
    type: ArtifactType
    uri: str = Field(sa_column=Column(TEXT, nullable=False))
    materializer: str = Field(sa_column=Column(TEXT, nullable=False))
    data_type: str = Field(sa_column=Column(TEXT, nullable=False))
    tags: List["TagResourceSchema"] = Relationship(
        back_populates="artifact_version",
        sa_relationship_kwargs=dict(
            primaryjoin=f"and_(TagResourceSchema.resource_type=='{TaggableResourceTypes.ARTIFACT_VERSION.value}', foreign(TagResourceSchema.resource_id)==ArtifactVersionSchema.id)",
            cascade="delete",
            overlaps="tags",
        ),
    )

    # Foreign keys
    artifact_id: UUID = build_foreign_key_field(
        source=__tablename__,
        target=ArtifactSchema.__tablename__,
        source_column="artifact_id",
        target_column="id",
        ondelete="CASCADE",
        nullable=False,
    )
    artifact_store_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=StackComponentSchema.__tablename__,
        source_column="artifact_store_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    user_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=UserSchema.__tablename__,
        source_column="user_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    workspace_id: UUID = build_foreign_key_field(
        source=__tablename__,
        target=WorkspaceSchema.__tablename__,
        source_column="workspace_id",
        target_column="id",
        ondelete="CASCADE",
        nullable=False,
    )

    # Relationships
    artifact: "ArtifactSchema" = Relationship(back_populates="versions")
    user: Optional["UserSchema"] = Relationship(
        back_populates="artifact_versions"
    )
    workspace: "WorkspaceSchema" = Relationship(
        back_populates="artifact_versions"
    )
    run_metadata: List["RunMetadataSchema"] = Relationship(
        back_populates="artifact_version",
        sa_relationship_kwargs=dict(
            primaryjoin=f"and_(RunMetadataSchema.resource_type=='{MetadataResourceTypes.ARTIFACT_VERSION.value}', foreign(RunMetadataSchema.resource_id)==ArtifactVersionSchema.id)",
            cascade="delete",
            overlaps="run_metadata",
        ),
    )
    output_of_step_runs: List["StepRunOutputArtifactSchema"] = Relationship(
        back_populates="artifact_version",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    input_of_step_runs: List["StepRunInputArtifactSchema"] = Relationship(
        back_populates="artifact_version",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    visualizations: List["ArtifactVisualizationSchema"] = Relationship(
        back_populates="artifact_version",
        sa_relationship_kwargs={"cascade": "delete"},
    )
    model_versions_artifacts_links: List[
        "ModelVersionArtifactSchema"
    ] = Relationship(
        back_populates="artifact_version",
        sa_relationship_kwargs={"cascade": "delete"},
    )

    @classmethod
    def from_request(
        cls,
        artifact_version_request: ArtifactVersionRequest,
    ) -> "ArtifactVersionSchema":
        """Convert an `ArtifactVersionRequest` to an `ArtifactVersionSchema`.

        Args:
            artifact_version_request: The request model to convert.

        Returns:
            The converted schema.
        """
        try:
            version_number = int(artifact_version_request.version)
        except ValueError:
            version_number = None
        return cls(
            artifact_id=artifact_version_request.artifact_id,
            version=str(artifact_version_request.version),
            version_number=version_number,
            artifact_store_id=artifact_version_request.artifact_store_id,
            workspace_id=artifact_version_request.workspace,
            user_id=artifact_version_request.user,
            type=artifact_version_request.type,
            uri=artifact_version_request.uri,
            materializer=artifact_version_request.materializer.json(),
            data_type=artifact_version_request.data_type.json(),
        )

    def to_model(self, hydrate: bool = False) -> ArtifactVersionResponse:
        """Convert an `ArtifactVersionSchema` to an `ArtifactVersionResponse`.

        Args:
            hydrate: bool to decide whether to return a hydrated version of the
                model.

        Returns:
            The created `ArtifactVersionResponse`.
        """
        try:
            materializer = Source.parse_raw(self.materializer)
        except ValidationError:
            # This is an old source which was an importable source path
            materializer = Source.from_import_path(self.materializer)

        try:
            data_type = Source.parse_raw(self.data_type)
        except ValidationError:
            # This is an old source which was an importable source path
            data_type = Source.from_import_path(self.data_type)

        # Create the body of the model
        body = ArtifactVersionResponseBody(
            artifact=self.artifact.to_model(),
            version=self.version_number or self.version,
            user=self.user.to_model() if self.user else None,
            uri=self.uri,
            type=self.type,
            materializer=materializer,
            data_type=data_type,
            created=self.created,
            updated=self.updated,
        )

        # Create the metadata of the model
        metadata = None
        if hydrate:
            producer_step_run_id = None
            if self.output_of_step_runs:
                step_run = self.output_of_step_runs[0].step_run
                if step_run.status == ExecutionStatus.COMPLETED:
                    producer_step_run_id = step_run.id
                else:
                    producer_step_run_id = step_run.original_step_run_id

            metadata = ArtifactVersionResponseMetadata(
                workspace=self.workspace.to_model(),
                artifact_store_id=self.artifact_store_id,
                producer_step_run_id=producer_step_run_id,
                visualizations=[v.to_model() for v in self.visualizations],
                run_metadata={m.key: m.to_model() for m in self.run_metadata},
                tags=[t.tag.to_model() for t in self.tags],
            )

        return ArtifactVersionResponse(
            id=self.id,
            body=body,
            metadata=metadata,
        )

    def update(
        self, artifact_version_update: ArtifactVersionUpdate
    ) -> "ArtifactVersionSchema":
        """Update an `ArtifactVersionSchema` with an `ArtifactVersionUpdate`.

        Args:
            artifact_version_update: The update model to apply.

        Returns:
            The updated `ArtifactVersionSchema`.
        """
        self.updated = datetime.utcnow()
        return self
