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
"""External artifact definition."""
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import BaseModel, PrivateAttr

from zenml.logger import get_logger
from zenml.models.v2.core.artifact import ArtifactResponse

if TYPE_CHECKING:
    from zenml.model.model_version import ModelVersion

logger = get_logger(__name__)


class ExternalArtifactConfiguration(BaseModel):
    """External artifact configuration.

    Lightweight class to pass in the steps for runtime inference.
    """

    id: Optional[UUID] = None
    name: Optional[str] = None
    version: Optional[str] = None

    _model_version: Optional["ModelVersion"] = PrivateAttr(None)

    def _set_model_version(self, model_version: "ModelVersion") -> None:
        self._model_version = model_version

    def get_artifact_version_id(self) -> UUID:
        """Get the artifact.

        Returns:
            The artifact ID.

        Raises:
            RuntimeError: If the artifact store of the referenced artifact
                is not the same as the one in the active stack.
            RuntimeError: If neither the ID nor the name of the artifact was
                provided.
        """
        from zenml.client import Client

        client = Client()

        if self.id:
            response = client.get_artifact_version(self.id)
        elif self.name:
            if self.version:
                response = client.get_artifact_version(
                    self.name, version=self.version
                )
            elif self._model_version:
                response_ = self._model_version.get_artifact(self.name)
                if not isinstance(response_, ArtifactResponse):
                    raise RuntimeError(
                        f"Failed to pull artifact `{self.name}` from the Model "
                        f"Version (name=`{self._model_version.name}`, version="
                        f"`{self._model_version.version}`). Please validate the "
                        "input and try again."
                    )
                response = response_
            else:
                response = client.get_artifact_version(self.name)
        else:
            raise RuntimeError(
                "Either the ID or name of the artifact must be provided. "
                "If you created this ExternalArtifact from a value, please "
                "ensure that `upload_by_value` was called before trying to "
                "fetch the artifact ID."
            )

        artifact_store_id = client.active_stack.artifact_store.id
        if response.artifact_store_id != artifact_store_id:
            raise RuntimeError(
                f"The artifact {response.name} (ID: {response.id}) "
                "referenced by an external artifact is not stored in the "
                "artifact store of the active stack. This will lead to "
                "issues loading the artifact. Please make sure to only "
                "reference artifact versions stored in your active artifact "
                "store."
            )

        self.id = response.id

        return self.id
