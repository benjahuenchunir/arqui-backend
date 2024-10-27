import os

from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction


class WebpayPlusTransaction:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebpayPlusTransaction, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if os.getenv("ENV") == "production":
            self.tx = Transaction(
                WebpayOptions(
                    IntegrationCommerceCodes.WEBPAY_PLUS,
                    IntegrationApiKeys.WEBPAY,
                    IntegrationType.LIVE,
                )
            )
        else:
            self.tx = Transaction(
                WebpayOptions(
                    IntegrationCommerceCodes.WEBPAY_PLUS,
                    IntegrationApiKeys.WEBPAY,
                    IntegrationType.TEST,
                )
            )


webpay_plus_transaction = WebpayPlusTransaction().tx
