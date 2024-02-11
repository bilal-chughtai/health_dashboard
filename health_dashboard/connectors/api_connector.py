class APIConnector:
    def __init__(self, access_token: str):
        """
        Initialize the API connector with an access token.

        :param access_token: The access token for authentication.
        """
        self.access_token = access_token

    def fetch_data(self):
        """
        Placeholder method for fetching data. Specific connectors will implement this method.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
