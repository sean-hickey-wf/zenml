#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
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
"""Models representing model versions."""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional, Type, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, Field, PrivateAttr, validator

from zenml.constants import STR_FIELD_MAX_LENGTH, TEXT_FIELD_MAX_LENGTH
from zenml.enums import ModelStages
from zenml.models.v2.base.filter import AnyQuery
from zenml.models.v2.base.scoped import (
    WorkspaceScopedFilter,
    WorkspaceScopedRequest,
    WorkspaceScopedResponse,
    WorkspaceScopedResponseBody,
    WorkspaceScopedResponseMetadata,
)

if TYPE_CHECKING:
    from zenml.model.model_version import ModelVersion
    from zenml.models.v2.core.artifact_version import ArtifactVersionResponse
    from zenml.models.v2.core.model import ModelResponse
    from zenml.models.v2.core.pipeline_run import PipelineRunResponse
    from zenml.zen_stores.schemas import BaseSchema

    AnySchema = TypeVar("AnySchema", bound=BaseSchema)


# ------------------ Request Model ------------------


class ModelVersionRequest(WorkspaceScopedRequest):
    """Request model for model versions."""

    name: Optional[str] = Field(
        description="The name of the model version",
        max_length=STR_FIELD_MAX_LENGTH,
        default=None,
    )
    description: Optional[str] = Field(
        description="The description of the model version",
        max_length=TEXT_FIELD_MAX_LENGTH,
        default=None,
    )
    stage: Optional[str] = Field(
        description="The stage of the model version",
        max_length=STR_FIELD_MAX_LENGTH,
        default=None,
    )

    number: Optional[int] = Field(
        description="The number of the model version",
    )
    model: UUID = Field(
        description="The ID of the model containing version",
    )


# ------------------ Update Model ------------------


class ModelVersionUpdate(BaseModel):
    """Update model for model versions."""

    model: UUID = Field(
        description="The ID of the model containing version",
    )
    stage: Optional[Union[str, ModelStages]] = Field(
        description="Target model version stage to be set", default=None
    )
    force: bool = Field(
        description="Whether existing model version in target stage should be "
        "silently archived or an error should be raised.",
        default=False,
    )
    name: Optional[str] = Field(
        description="Target model version name to be set", default=None
    )

    @validator("stage")
    def _validate_stage(cls, stage: str) -> str:
        stage = getattr(stage, "value", stage)
        if stage is not None and stage not in [
            stage.value for stage in ModelStages
        ]:
            raise ValueError(f"`{stage}` is not a valid model stage.")
        return stage


# ------------------ Response Model ------------------


class ModelVersionResponseBody(WorkspaceScopedResponseBody):
    """Response body for model versions."""

    stage: Optional[str] = Field(
        description="The stage of the model version",
        max_length=STR_FIELD_MAX_LENGTH,
        default=None,
    )
    number: int = Field(
        description="The number of the model version",
    )
    model: "ModelResponse" = Field(
        description="The model containing version",
    )
    model_artifact_ids: Dict[str, Dict[str, UUID]] = Field(
        description="Model artifacts linked to the model version",
        default={},
    )
    data_artifact_ids: Dict[str, Dict[str, UUID]] = Field(
        description="Data artifacts linked to the model version",
        default={},
    )
    endpoint_artifact_ids: Dict[str, Dict[str, UUID]] = Field(
        description="Endpoint artifacts linked to the model version",
        default={},
    )
    pipeline_run_ids: Dict[str, UUID] = Field(
        description="Pipeline runs linked to the model version",
        default={},
    )
    created: datetime = Field(
        title="The timestamp when this component was created."
    )
    updated: datetime = Field(
        title="The timestamp when this component was last updated.",
    )


class ModelVersionResponseMetadata(WorkspaceScopedResponseMetadata):
    """Response metadata for model versions."""

    description: Optional[str] = Field(
        description="The description of the model version",
        max_length=TEXT_FIELD_MAX_LENGTH,
        default=None,
    )


class ModelVersionResponse(
    WorkspaceScopedResponse[
        ModelVersionResponseBody, ModelVersionResponseMetadata
    ]
):
    """Response model for model versions."""

    name: Optional[str] = Field(
        description="The name of the model version",
        max_length=STR_FIELD_MAX_LENGTH,
        default=None,
    )

    @property
    def stage(self) -> Optional[str]:
        """The `stage` property.

        Returns:
            the value of the property.
        """
        return self.get_body().stage

    @property
    def number(self) -> int:
        """The `number` property.

        Returns:
            the value of the property.
        """
        return self.get_body().number

    @property
    def model(self) -> "ModelResponse":
        """The `model` property.

        Returns:
            the value of the property.
        """
        return self.get_body().model

    @property
    def model_artifact_ids(self) -> Dict[str, Dict[str, UUID]]:
        """The `model_artifact_ids` property.

        Returns:
            the value of the property.
        """
        return self.get_body().model_artifact_ids

    @property
    def data_artifact_ids(self) -> Dict[str, Dict[str, UUID]]:
        """The `data_artifact_ids` property.

        Returns:
            the value of the property.
        """
        return self.get_body().data_artifact_ids

    @property
    def endpoint_artifact_ids(self) -> Dict[str, Dict[str, UUID]]:
        """The `endpoint_artifact_ids` property.

        Returns:
            the value of the property.
        """
        return self.get_body().endpoint_artifact_ids

    @property
    def pipeline_run_ids(self) -> Dict[str, UUID]:
        """The `pipeline_run_ids` property.

        Returns:
            the value of the property.
        """
        return self.get_body().pipeline_run_ids

    @property
    def created(self) -> datetime:
        """The `created` property.

        Returns:
            the value of the property.
        """
        return self.get_body().created

    @property
    def updated(self) -> datetime:
        """The `updated` property.

        Returns:
            the value of the property.
        """
        return self.get_body().updated

    @property
    def description(self) -> Optional[str]:
        """The `description` property.

        Returns:
            the value of the property.
        """
        return self.get_metadata().description

    def get_hydrated_version(self) -> "ModelVersionResponse":
        """Get the hydrated version of this model version.

        Returns:
            an instance of the same entity with the metadata field attached.
        """
        from zenml.client import Client

        return Client().zen_store.get_model_version(self.id)

    # Helper functions
    def to_model_version(
        self,
        was_created_in_this_run: bool = False,
        suppress_class_validation_warnings: bool = False,
    ) -> "ModelVersion":
        """Convert response model to ModelVersion object.

        Args:
            was_created_in_this_run: Whether model version was created during
                the current run.
            suppress_class_validation_warnings: internally used to suppress
                repeated warnings.

        Returns:
            ModelVersion object
        """
        from zenml.model.model_version import ModelVersion

        mv = ModelVersion(
            name=self.model.name,
            license=self.model.license,
            description=self.description,
            audience=self.model.audience,
            use_cases=self.model.use_cases,
            limitations=self.model.limitations,
            trade_offs=self.model.trade_offs,
            ethics=self.model.ethics,
            tags=[t.name for t in self.model.tags],
            version=self.name,
            was_created_in_this_run=was_created_in_this_run,
            suppress_class_validation_warnings=suppress_class_validation_warnings,
        )
        mv._id = self.id

        return mv

    @property
    def model_artifacts(
        self,
    ) -> Dict[str, Dict[str, "ArtifactVersionResponse"]]:
        """Get all model artifacts linked to this model version.

        Returns:
            Dictionary of model artifacts with versions as
            Dict[str, Dict[str, ArtifactResponse]]
        """
        from zenml.client import Client

        return {
            name: {
                version: Client().get_artifact_version(a)
                for version, a in self.model_artifact_ids[name].items()
            }
            for name in self.model_artifact_ids
        }

    @property
    def data_artifacts(
        self,
    ) -> Dict[str, Dict[str, "ArtifactVersionResponse"]]:
        """Get all data artifacts linked to this model version.

        Returns:
            Dictionary of data artifacts with versions as
            Dict[str, Dict[str, ArtifactResponse]]
        """
        from zenml.client import Client

        return {
            name: {
                version: Client().get_artifact_version(a)
                for version, a in self.data_artifact_ids[name].items()
            }
            for name in self.data_artifact_ids
        }

    @property
    def endpoint_artifacts(
        self,
    ) -> Dict[str, Dict[str, "ArtifactVersionResponse"]]:
        """Get all endpoint artifacts linked to this model version.

        Returns:
            Dictionary of endpoint artifacts with versions as
            Dict[str, Dict[str, ArtifactResponse]]
        """
        from zenml.client import Client

        return {
            name: {
                version: Client().get_artifact_version(a)
                for version, a in self.endpoint_artifact_ids[name].items()
            }
            for name in self.endpoint_artifact_ids
        }

    @property
    def pipeline_runs(self) -> Dict[str, "PipelineRunResponse"]:
        """Get all pipeline runs linked to this version.

        Returns:
            Dictionary of Pipeline Runs as PipelineRunResponseModel
        """
        from zenml.client import Client

        return {
            name: Client().get_pipeline_run(pr)
            for name, pr in self.pipeline_run_ids.items()
        }

    def _get_linked_object(
        self,
        collection: Dict[str, Dict[str, UUID]],
        name: str,
        version: Optional[str] = None,
    ) -> Optional["ArtifactVersionResponse"]:
        """Get the artifact linked to this model version given type.

        Args:
            collection: The collection to search in (one of
                self.model_artifact_ids, self.data_artifact_ids,
                self.endpoint_artifact_ids)
            name: The name of the artifact to retrieve.
            version: The version of the artifact to retrieve (None for
                latest/non-versioned)

        Returns:
            Specific version of an artifact from collection or None
        """
        from zenml.client import Client

        client = Client()

        if name not in collection:
            return None
        if version is None:
            version = max(collection[name].keys())
        return client.get_artifact_version(collection[name][version])

    def get_artifact(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional["ArtifactVersionResponse"]:
        """Get the artifact linked to this model version.

        Args:
            name: The name of the artifact to retrieve.
            version: The version of the artifact to retrieve (None for
                latest/non-versioned)

        Returns:
            Specific version of an artifact or None
        """
        all_artifact_ids = {
            **self.model_artifact_ids,
            **self.data_artifact_ids,
            **self.endpoint_artifact_ids,
        }
        return self._get_linked_object(all_artifact_ids, name, version)

    def get_model_artifact(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional["ArtifactVersionResponse"]:
        """Get the model artifact linked to this model version.

        Args:
            name: The name of the model artifact to retrieve.
            version: The version of the model artifact to retrieve (None for
                latest/non-versioned)

        Returns:
            Specific version of the model artifact or None
        """
        return self._get_linked_object(self.model_artifact_ids, name, version)

    def get_data_artifact(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional["ArtifactVersionResponse"]:
        """Get the data artifact linked to this model version.

        Args:
            name: The name of the data artifact to retrieve.
            version: The version of the data artifact to retrieve (None for
                latest/non-versioned)

        Returns:
            Specific version of the data artifact or None
        """
        return self._get_linked_object(
            self.data_artifact_ids,
            name,
            version,
        )

    def get_endpoint_artifact(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional["ArtifactVersionResponse"]:
        """Get the endpoint artifact linked to this model version.

        Args:
            name: The name of the endpoint artifact to retrieve.
            version: The version of the endpoint artifact to retrieve (None for
                latest/non-versioned)

        Returns:
            Specific version of the endpoint artifact or None
        """
        return self._get_linked_object(
            self.endpoint_artifact_ids,
            name,
            version,
        )

    def get_pipeline_run(self, name: str) -> "PipelineRunResponse":
        """Get pipeline run linked to this version.

        Args:
            name: The name of the pipeline run to retrieve.

        Returns:
            PipelineRun as PipelineRunResponseModel
        """
        from zenml.client import Client

        return Client().get_pipeline_run(self.pipeline_run_ids[name])

    def set_stage(
        self, stage: Union[str, ModelStages], force: bool = False
    ) -> None:
        """Sets this Model Version to a desired stage.

        Args:
            stage: the target stage for model version.
            force: whether to force archiving of current model version in
                target stage or raise.

        Raises:
            ValueError: if model_stage is not valid.
        """
        from zenml.client import Client

        stage = getattr(stage, "value", stage)
        if stage not in [stage.value for stage in ModelStages]:
            raise ValueError(f"`{stage}` is not a valid model stage.")

        Client().update_model_version(
            model_name_or_id=self.model.id,
            version_name_or_id=self.id,
            stage=stage,
            force=force,
        )

    # TODO in https://zenml.atlassian.net/browse/OSS-2433
    # def generate_model_card(self, template_name: str) -> str:
    #     """Return HTML/PDF based on input template"""


# ------------------ Filter Model ------------------


class ModelVersionFilter(WorkspaceScopedFilter):
    """Filter model for model versions."""

    name: Optional[str] = Field(
        default=None,
        description="The name of the Model Version",
    )
    number: Optional[int] = Field(
        default=None,
        description="The number of the Model Version",
    )
    workspace_id: Optional[Union[UUID, str]] = Field(
        default=None, description="The workspace of the Model Version"
    )
    user_id: Optional[Union[UUID, str]] = Field(
        default=None, description="The user of the Model Version"
    )
    stage: Optional[Union[str, ModelStages]] = Field(
        description="The model version stage", default=None
    )

    _model_id: UUID = PrivateAttr(None)

    def set_scope_model(self, model_name_or_id: Union[str, UUID]) -> None:
        """Set the model to scope this response.

        Args:
            model_name_or_id: The model to scope this response to.
        """
        try:
            model_id = UUID(str(model_name_or_id))
        except ValueError:
            from zenml.client import Client

            model_id = Client().get_model(model_name_or_id).id

        self._model_id = model_id

    def apply_filter(
        self,
        query: AnyQuery,
        table: Type["AnySchema"],
    ) -> AnyQuery:
        """Applies the filter to a query.

        Args:
            query: The query to which to apply the filter.
            table: The query table.

        Returns:
            The query with filter applied.
        """
        query = super().apply_filter(query=query, table=table)

        if self._model_id:
            query = query.where(getattr(table, "model_id") == self._model_id)

        return query
