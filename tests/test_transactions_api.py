import pytest
import requests
from datetime import datetime
from jsonschema import validate, ValidationError
from dotenv import load_dotenv
import os
from utils import custom_logger as cl

# Loads BASE_URL and Headers stored as env variables
load_dotenv()

log = cl.customLogger()
# Test configuration
BASE_URL = os.getenv("BASE_URL")
HEADERS = {
    "host": os.getenv("host")
}

# Test customer IDs for different scenarios
CUSTOMERS = {
    "Customer1": "b3c8f5d2-4a6e-4c0b-9f7d-8f1c2e3a4b5c",  # Customer with no transactions
    "Customer2": "746c51bc-bdb9-44d2-9a3e-c4715bc91ee4",  # Will return upto 5 transactions with expected behaviour
    "Customer3": "5723a60b-b7f5-4259-b670-43bd3be1cf90",  # Will return upto 5 transactions with unexpected behaviours
    "Customer4": "13ef28a8-9488-4d19-ba2f-3ff44912c5e8",  # Will return upto 5 transactions with unexpected behaviours
    "Customer5": "0828a547-f4bf-433a-b3ef-0dc70d6bad8a"  # Will return upto 5 transactions with unexpected behaviours
}

transaction_schema = {
    "type": "object",
    "required": [
        "transactionId", "amount", "currency", "merchantName", "timestamp",
        "type", "subType", "status", "categoryId", "description"
    ],
    "properties": {
        "transactionId": {"type": "string"},
        "amount": {"type": "number"},
        "currency": {"type": "string"},
        "merchantName": {"type": ["string", "null"]},
        "timestamp": {
            "type": "string",
            "format": "date-time"
        },
        "type": {"type": "string", "enum": ["Debit", "Credit"]},
        "subType": {"type": "string"},
        "status": {"type": "string", "enum": ["Pending", "Booked"]},
        "categoryId": {"type": "integer", "minimum": 1, "maximum": 20},
        "description": {"type": "string"}
    },
    "additionalProperties": False
}


class TestTransactionsAPI:
    def make_request(self, customer_id, **params):
        """
        Helper method to make GET request with given customer ID and optional query params.
        """
        params['customerId'] = customer_id
        for key, value in params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
        return requests.get(BASE_URL, headers=HEADERS, params=params)

    def validate_transaction_structure(self, transaction):
        """
        Validates a single transaction object against the predefined JSON Schema.
        """
        try:
            validate(instance=transaction, schema=transaction_schema)
        except ValidationError as e:
            log.error(f"Schema validation failed: {e.message}")
            pytest.fail(f"Schema validation error: {e.message}")

    def validate_transaction_ordering(self, transactions):
        """
        Validates that transactions are ordered with all 'Pending' first, and each group sorted by timestamp descending.
        """
        try:
            if len(transactions) <= 1:
                return

            # Split transactions into Pending and Booked groups
            pending = [t for t in transactions if t['status'] == 'Pending']
            booked = [t for t in transactions if t['status'] == 'Booked']

            # Pending transactions must appear before any Booked ones
            for i in range(len(pending)):
                assert transactions[i]['status'] == 'Pending'

            # Within each group, timestamps must be in descending order
            for group in [pending, booked]:
                for i in range(len(group) - 1):
                    t1 = datetime.fromisoformat(group[i]['timestamp'].replace('Z', '+00:00'))
                    t2 = datetime.fromisoformat(group[i + 1]['timestamp'].replace('Z', '+00:00'))
                    assert t1 >= t2
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    def test_get_all_transactions_empty_customer(self):
        """
        Validate that a customer with no transactions returns an empty list.
        """
        try:
            response = self.make_request(CUSTOMERS["Customer1"])
            assert response.status_code == 200
            assert response.headers.get('content-type') == 'application/json'
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
            log.info("✅ Test passed: test_get_all_transactions_empty_customer")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    def test_get_all_transactions_normal_customer(self):
        """
        Validate correct structure, count and ordering of transactions for a normal customer.
        """
        try:
            response = self.make_request(CUSTOMERS["Customer2"])
            assert response.status_code == 200
            assert response.headers.get('content-type') == 'application/json'
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 5

            for tx in data:
                self.validate_transaction_structure(tx)
            self.validate_transaction_ordering(data)
            log.info("✅ Test passed: test_get_all_transactions_normal_customer")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    def test_invalid_customer_id(self):
        """
        Validate that an invalid customer ID returns appropriate 400 response and error message.
        """
        try:
            response = self.make_request("invalid-customer-id")
            assert response.status_code == 400
            assert response.text == '"Invalid customerId guid format"'
            assert response.headers.get('content-type') == 'application/json'
            log.info("✅ Test passed: test_invalid_customer_id")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    def test_missing_customer_id(self):
        """
        Validate that missing customer ID results in a 400 response.
        """
        try:
            response = requests.get(BASE_URL, headers=HEADERS)
            assert response.status_code == 400
            assert response.text == '"Missing customerId query parameter"'
            assert response.headers.get('content-type') == 'application/json'
            log.info("✅ Test passed: test_missing_customer_id")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise



    def test_filter_by_category(self):
        """
        Validate that transactions can be filtered by categoryId correctly.
        """
        try:
            response = self.make_request(CUSTOMERS["Customer2"], categoryId=11)
            assert response.status_code == 200
            data = response.json()

            for tx in data:
                assert tx['categoryId'] == 11
                log.info("✅ Test passed: test_filter_by_category")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    def test_filter_exclude_pending(self):
        """
        Validate that includePending=False filters out all 'Pending' transactions.
        """
        try:
            response = self.make_request(CUSTOMERS["Customer2"], includePending=False)
            assert response.status_code == 200
            data = response.json()

            for tx in data:
                assert tx['status'] != 'Pending'
                log.info("✅ Test passed: test_filter_exclude_pending")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    def test_filter_by_date_range(self):
        """
        Validate date range filtering using fromDate and toDate parameters.
        """
        try:
            response = self.make_request(CUSTOMERS["Customer2"], fromDate="2025-06-04", toDate="2025-06-05")
            assert response.status_code == 200
            data = response.json()

            for tx in data:
                tx_date = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00')).date()
                assert datetime(2025, 6, 4).date() <= tx_date <= datetime(2025, 6, 5).date()
                log.info("✅ Test passed: test_filter_by_date_range")
        except AssertionError as e:
            log.error(f"❌ Assertion failed {e}")
            raise

    @pytest.mark.parametrize("customer_key", ["Customer2", "Customer3", "Customer4", "Customer5"])
    def test_transaction_structure_consistency(self, customer_key):
        """
        Parametrized test to ensure all customers return valid transaction structures.
        """
        try:
            response = self.make_request(CUSTOMERS[customer_key])
            assert response.status_code == 200
            data = response.json()

            for tx in data:
                self.validate_transaction_structure(tx)
            log.info(f"✅ Test passed: test_transaction_structure_consistency for {customer_key}")
        except AssertionError as e:
            log.error(f"❌ Assertion failed for {customer_key} due to {e}")
            raise

    @pytest.mark.parametrize("customer_key", ["Customer2", "Customer3", "Customer4", "Customer5"])
    def test_transaction_ordering_consistency(self, customer_key):
        """
        Parametrized test to ensure transaction ordering is consistent for all customers.
        """
        try:
            response = self.make_request(CUSTOMERS[customer_key])
            assert response.status_code == 200
            data = response.json()

            self.validate_transaction_ordering(data)
            log.info(f"✅ Test passed: test_transaction_ordering_consistency for {customer_key}")
        except AssertionError as e:
            log.error(f"❌ Assertion failed for {customer_key} due to {e}")
            raise

    @pytest.mark.parametrize("customer_key", ["Customer2", "Customer3", "Customer4", "Customer5"])
    def test_amount_sign_consistency(self, customer_key):
        """
        Ensure Debits have negative amounts and Credits have positive amounts.
        """
        try:
            response = self.make_request(CUSTOMERS[customer_key])
            assert response.status_code == 200
            data = response.json()

            for tx in data:
                if tx['type'] == 'Debit':
                    assert tx['amount'] < 0, f"Debit should be negative: {tx['transactionId']}"
                elif tx['type'] == 'Credit':
                    assert tx['amount'] > 0, f"Credit should be positive: {tx['transactionId']}"
            log.info(f"✅ Test passed: test_amount_sign_consistency for {customer_key}")
        except AssertionError as e:
            log.error(f"❌ Assertion failed for {customer_key} due to {e}")
            raise


    @pytest.mark.parametrize("customer_key", ["Customer2", "Customer3", "Customer4", "Customer5"])
    def test_filter_behavior_consistency(self, customer_key):
        """
        Ensure that includePending=True returns all transactions,
        and includePending=False filters out 'Pending' ones.
        """
        try:
            r1 = self.make_request(CUSTOMERS[customer_key], includePending=True)
            r2 = self.make_request(CUSTOMERS[customer_key], includePending=False)

            assert r1.status_code == 200
            assert r2.status_code == 200

            data1 = r1.json()
            data2 = r2.json()

            assert len(data2) <= len(data1)

            for tx in data2:
                assert tx['status'] != 'Pending'
            log.info(f"✅ Test passed: test_filter_behavior_consistency for {customer_key}")
        except AssertionError as e:
            log.error(f"❌ Assertion failed for {customer_key} due to {e}")
            raise
