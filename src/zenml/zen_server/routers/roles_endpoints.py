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
"""Endpoint definitions for roles and role assignment."""
from typing import Union
from uuid import UUID

from fastapi import APIRouter, Depends, Security

from zenml.constants import API, ROLES, VERSION_1
from zenml.enums import PermissionType
from zenml.models import (
    Page,
    RoleFilter,
    RoleRequest,
    RoleResponse,
    RoleUpdate,
)
from zenml.zen_server.auth import AuthContext, authorize
from zenml.zen_server.exceptions import error_response
from zenml.zen_server.utils import (
    handle_exceptions,
    make_dependable,
    zen_store,
)

router = APIRouter(
    prefix=API + VERSION_1 + ROLES,
    tags=["roles"],
    responses={401: error_response},
)


@router.get(
    "",
    response_model=Page[RoleResponse],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_roles(
    role_filter_model: RoleFilter = Depends(make_dependable(RoleFilter)),
    hydrate: bool = False,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[RoleResponse]:
    """Returns a list of all roles.

    Args:
        role_filter_model: Filter model used for pagination, sorting, filtering
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        List of all roles.
    """
    return zen_store().list_roles(
        role_filter_model=role_filter_model, hydrate=hydrate
    )


@router.post(
    "",
    response_model=RoleResponse,
    responses={401: error_response, 409: error_response, 422: error_response},
)
@handle_exceptions
def create_role(
    role: RoleRequest,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> RoleResponse:
    """Creates a role.

    # noqa: DAR401

    Args:
        role: Role to create.

    Returns:
        The created role.
    """
    return zen_store().create_role(role=role)


@router.get(
    "/{role_name_or_id}",
    response_model=RoleResponse,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_role(
    role_name_or_id: Union[str, UUID],
    hydrate: bool = True,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> RoleResponse:
    """Returns a specific role.

    Args:
        role_name_or_id: Name or ID of the role.
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        A specific role.
    """
    return zen_store().get_role(
        role_name_or_id=role_name_or_id, hydrate=hydrate
    )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    responses={401: error_response, 409: error_response, 422: error_response},
)
@handle_exceptions
def update_role(
    role_id: UUID,
    role_update: RoleUpdate,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> RoleResponse:
    """Updates a role.

    # noqa: DAR401

    Args:
        role_id: The ID of the role.
        role_update: Role update.

    Returns:
        The created role.
    """
    return zen_store().update_role(role_id=role_id, role_update=role_update)


@router.delete(
    "/{role_name_or_id}",
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def delete_role(
    role_name_or_id: Union[str, UUID],
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> None:
    """Deletes a specific role.

    Args:
        role_name_or_id: Name or ID of the role.
    """
    zen_store().delete_role(role_name_or_id=role_name_or_id)
