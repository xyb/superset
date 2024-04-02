# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from flask import g, redirect, Response
from flask_appbuilder.api import expose, safe
from flask_jwt_extended.exceptions import NoAuthorizationError

from superset import app, security_manager
from superset.extensions import db
from superset.models.user_attributes import UserAttribute
from superset.utils.slack import get_slack_client
from superset.views.base_api import BaseSupersetApi
from superset.views.users.schemas import UserResponseSchema
from superset.views.utils import bootstrap_user_data

user_response_schema = UserResponseSchema()


class CurrentUserRestApi(BaseSupersetApi):
    """An API to get information about the current user"""

    resource_name = "me"
    openapi_spec_tag = "Current User"
    openapi_spec_component_schemas = (UserResponseSchema,)

    @expose("/", methods=("GET",))
    @safe
    def get_me(self) -> Response:
        """Get the user object corresponding to the agent making the request.
        ---
        get:
          summary: Get the user object
          description: >-
            Gets the user object corresponding to the agent making the request,
            or returns a 401 error if the user is unauthenticated.
          responses:
            200:
              description: The current user
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      result:
                        $ref: '#/components/schemas/UserResponseSchema'
            401:
              $ref: '#/components/responses/401'
        """
        try:
            if g.user is None or g.user.is_anonymous:
                return self.response_401()
        except NoAuthorizationError:
            return self.response_401()

        return self.response(200, result=user_response_schema.dump(g.user))

    @expose("/roles/", methods=("GET",))
    @safe
    def get_my_roles(self) -> Response:
        """Get the user roles corresponding to the agent making the request.
        ---
        get:
          summary: Get the user roles
          description: >-
            Gets the user roles corresponding to the agent making the request,
            or returns a 401 error if the user is unauthenticated.
          responses:
            200:
              description: The current user
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      result:
                        $ref: '#/components/schemas/UserResponseSchema'
            401:
              $ref: '#/components/responses/401'
        """
        try:
            if g.user is None or g.user.is_anonymous:
                return self.response_401()
        except NoAuthorizationError:
            return self.response_401()
        user = bootstrap_user_data(g.user, include_perms=True)
        return self.response(200, result=user)


class UserRestApi(BaseSupersetApi):
    """An API to get information about users"""

    resource_name = "user"
    openapi_spec_tag = "User"
    openapi_spec_component_schemas = (UserResponseSchema,)

    @expose("/<user_id>/avatar.png", methods=("GET",))
    @safe
    def avatar(self, user_id: str) -> Response:
        """Get a redirect to the avatar's URL for the user with the given ID.
        ---
        get:
          summary: Get the user avatar
          description: >-
            Gets the avatar URL for the user with the given ID, or returns a 401 error
            if the user is unauthenticated.
          responses:
            301:
              description: A redirect to the user's avatar URL
            401:
              $ref: '#/components/responses/401'
            404:
              $ref: '#/components/responses/404'
        """
        try:
            avatar_url = None
            if not user_id:
                return self.response_401()

            # Fetching the user's avatar from the database
            user_attrs = (
                db.session.query(UserAttribute).filter_by(user_id=user_id).first()
            )

            if not user_attrs or not user_attrs.avatar_url:
                if app.config.get("SLACK_ENABLE_AVATARS"):
                    user = (
                        db.session.query(security_manager.user_model)
                        .filter_by(id=user_id)
                        .first()
                    )
                    # Fetching the user's avatar from slack
                    client = get_slack_client()
                    response = client.users_lookupByEmail(email=user.email)
                    avatar_url = (
                        response.data.get("user").get("profile").get("image_192")
                    )

                    # Saving the avatar url to the database
                    user_attrs = UserAttribute(user_id=user_id, avatar_url=avatar_url)
                    db.session.add(user_attrs)
                    db.session.commit()
            elif user_attrs:
                avatar_url = user_attrs.avatar_url

            if avatar_url:
                return redirect(avatar_url, code=301)

            return self.response_404()

        except NoAuthorizationError:
            return self.response_401()
