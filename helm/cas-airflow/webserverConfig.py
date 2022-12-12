from airflow.www.security import AirflowSecurityManager
import logging
from typing import Dict, Any, List, Union
import os
from flask_appbuilder.security.manager import AUTH_OAUTH

log = logging.getLogger(__name__)
log.setLevel(os.getenv("AIRFLOW__LOGGING__FAB_LOGGING_LEVEL", "INFO"))

## Define the security manager class to be used 

FAB_ADMIN_ROLE = "Admin"
FAB_VIEWER_ROLE = "Viewer"
FAB_PUBLIC_ROLE = "Public"  # The "Public" role is given no permissions
# This is the cas-developers team id
TEAM_ID_A_FROM_GITHUB = 3204518


def team_parser(team_payload: Dict[str, Any]) -> List[int]:
    # Parse the team payload from Github however you want here.
    printme = [team["name"] for team in team_payload]
    print(f"team ids: {printme}")
    return [team["id"] for team in team_payload]


def map_roles(team_list: List[int]) -> List[str]:
    # Associate the team IDs with Roles here.
    # The expected output is a list of roles that FAB will use to Authorize the user.

    team_role_map = {
        TEAM_ID_A_FROM_GITHUB: FAB_ADMIN_ROLE,
    }
    printthistoo = list(set(team_role_map.get(team, FAB_PUBLIC_ROLE) for team in team_list))
    print(' '.join(printthistoo))
    return list(set(team_role_map.get(team, FAB_PUBLIC_ROLE) for team in team_list))


class GithubTeamAuthorizer(AirflowSecurityManager):

    # In this example, the oauth provider == 'github'.
    # If you ever want to support other providers, see how it is done here:
    # https://github.com/dpgaspar/Flask-AppBuilder/blob/master/flask_appbuilder/security/manager.py#L550
    def get_oauth_user_info(
        self, provider: str, resp: Any
    ) -> Dict[str, Union[str, List[str]]]:

        # Creates the user info payload from Github.
        # The user previously allowed your app to act on thier behalf,
        #   so now we can query the user and teams endpoints for their data.
        # Username and team membership are added to the payload and returned to FAB.

        remote_app = self.appbuilder.sm.oauth_remotes[provider]
        me = remote_app.get("user")
        user_data = me.json()
        team_data = remote_app.get("user/teams")
        teams = team_parser(team_data.json())
        roles = map_roles(teams)
        # To do: remove unnecessary printf statements
        print(f"User info from Github: {user_data}\n" f"Team info from Github: {teams}")
        print(f"Team data: {team_data}")
        print(f"Team data: {teams}")
        
        log.debug(
            f"User info from Github: {user_data}\n" f"Team info from Github: {teams}"
        )
        x={"username": "github_" + user_data.get("login"), "role_keys": roles}
        print(f"auth class return: {x}")
        return {"username": "github_" + user_data.get("login"), "role_keys": roles}

AUTH_TYPE = AUTH_OAUTH
AUTH_ROLES_SYNC_AT_LOGIN = True  # Checks roles on every login
AUTH_USER_REGISTRATION = (
    True  # allow users who are not already in the FAB DB to register
)

FAB_SECURITY_MANAGER_CLASS = "webserverConfig.GithubTeamAuthorizer"

# If you wish, you can add multiple OAuth providers.
OAUTH_PROVIDERS = [
    {
        "name": "github",
        "icon": "fa-github",
        "token_key": "access_token",
        "remote_app": {
            "client_id": os.getenv("GH_CLIENT_ID"),
            "client_secret": os.getenv("GH_CLIENT_SECRET"),
            "api_base_url": "https://api.github.com",
            "client_kwargs": {"scope": "read:org, read:user"},
            "access_token_url": "https://github.com/login/oauth/access_token",
            "authorize_url": "https://github.com/login/oauth/authorize",
            "request_token_url": None,
        },
    },
]
