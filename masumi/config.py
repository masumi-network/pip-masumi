class Config:
    """
    Centralized configuration for the masumi_crewai package.
    """

    def __init__(self, payment_service_url: str, payment_api_key: str,
                 registry_service_url: str = None, registry_api_key: str = None,
                 preprod_address: str = None,
                 mainnet_address: str = None):
        self.payment_service_url = payment_service_url
        self.payment_api_key = payment_api_key
        self.registry_service_url = registry_service_url
        self.registry_api_key = registry_api_key
        self.preprod_address = preprod_address
        self.mainnet_address = mainnet_address
        self._validate()

    def _validate(self):
        """
        Validate that all required configuration parameters are set.
        Raises ValueError if any required parameter is missing.
        """
        import os
        
        required_configs = {
            "PAYMENT_SERVICE_URL": self.payment_service_url,
            "PAYMENT_API_KEY": self.payment_api_key,
        }

        missing_configs = [key for key, value in required_configs.items() if not value]
        if missing_configs:
            error_msg = f"Missing required configuration parameters: {', '.join(missing_configs)}\n\n"
            error_msg += "Please ensure these environment variables are set. You can:\n"
            error_msg += "1. Set them in your environment:\n"
            error_msg += f"   export {' '.join(missing_configs)}\n\n"
            error_msg += "2. Or add them to a .env file in your project directory:\n"
            for key in missing_configs:
                error_msg += f"   {key}=your_value_here\n"
            error_msg += "\nNote: The .env file should be in the same directory as your main.py file.\n"
            error_msg += f"Current working directory: {os.getcwd()}\n"
            raise ValueError(error_msg)