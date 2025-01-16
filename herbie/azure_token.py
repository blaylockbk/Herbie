import requests
from datetime import datetime, timezone


class AzureBlobToken:
    """Get a token for accessing Azure Blob Storage.

    This class fetches a token from the Planetary Computer SAS API.
    https://planetarycomputer.microsoft.com/docs/concepts/sas/

    Parameters
    ----------
    collection : str
        Name of the collection to get a token for.

    Attributes
    ----------
    collection : str
        Name of the collection.
    url : str
        URL to fetch the token from.
    token_data : dict
        Token data returned from the API.
    token : str
        The token string.
    expiry_time : datetime
        The expiry time of the token.
    """

    def __init__(self, collection):
        self.collection = collection
        self.url = (
            f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{collection}"
        )
        self.token_data = None
        self._fetch_token()

    def _fetch_token(self):
        """Fetch the token data from the URL and set attributes."""
        response = requests.get(self.url)
        if response.status_code == 200:
            self.token_data = response.json()
            for key, value in self.token_data.items():
                setattr(self, key.replace(":", "_"), value)
            self.expiry_time = datetime.strptime(
                self.msft_expiry, "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        else:
            raise Exception(
                f"Failed to fetch token: {response.status_code} {response.text}"
            )

    def _is_expired(self):
        """Check if the token has expired."""
        return datetime.now(timezone.utc) >= self.expiry_time

    def __str__(self):
        """Return the token string, refreshing it if expired."""
        if self._is_expired():
            self._fetch_token()
        return self.token

    def __add__(self, other):
        return f"{other}?{self.token}"

    def __radd__(self, other):
        return f"{other}?{self.token}"
