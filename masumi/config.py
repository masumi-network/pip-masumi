class Config:
    """
    Centralized configuration for the masumi package.

    Holds configuration values for payment service and network addresses.
    The payment service URL also hosts the registry endpoint (/registry/{agent-identifier}).
    For free agents (free_agent=True), payment credentials are optional.
    """

    def __init__(self, payment_service_url: str = None, payment_api_key: str = None,
                 registry_service_url: str = None, registry_api_key: str = None,
                 preprod_address: str = None,
                 mainnet_address: str = None,
                 free_agent: bool = False):
        self.payment_service_url = payment_service_url or ""
        self.payment_api_key = payment_api_key or ""
        self.registry_service_url = registry_service_url
        self.registry_api_key = registry_api_key
        self.preprod_address = preprod_address
        self.mainnet_address = mainnet_address
        self.free_agent = free_agent
        self._validate()

    def _validate(self):
        """
        Validate that all required configuration parameters are set.
        Raises ValueError if any required parameter is missing.
        
        For free agents, payment credentials are optional.
        For detailed diagnostics, use: masumi check
        """
        if self.free_agent:
            return  # Free agents skip payment service; no validation needed
        missing_configs = []
        if not self.payment_service_url:
            missing_configs.append("PAYMENT_SERVICE_URL")
        if not self.payment_api_key:
            missing_configs.append("PAYMENT_API_KEY")
        if missing_configs:
            error_msg = f"Missing required configuration parameters: {', '.join(missing_configs)}"
            error_msg += "\n\nRun 'masumi check' for detailed diagnostics and setup instructions."
            raise ValueError(error_msg)
