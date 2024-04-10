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

from flask import current_app
from slack_sdk import WebClient


def get_slack_client() -> WebClient:
    token: str = current_app.config["SLACK_API_TOKEN"]
    if callable(token):
        token = token()
    return WebClient(token=token, proxy=current_app.config["SLACK_PROXY"])


def get_user_avatar(email: str, client: WebClient = None) -> str:
    client = client or get_slack_client()
    response = client.users_lookupByEmail(email=email)
    avatar_url = response.data.get("user").get("profile").get("image_192")
    return avatar_url
