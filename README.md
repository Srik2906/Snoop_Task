# Project Overview

This project utilizes `pytest` and `Requests` Library to test a transactions api. It includes a GitHub Actions workflow for continuous integration, running tests on Manual Trigger.

```
├── .github/
│   └── workflows/
│       └── pytest.yaml  # GitHub Actions workflow for test automation
├── reports/
│   └── report.html                   # Generated Pytest HTML report
├── utils/
│   ├── __init__.py
│   └── custom_logger.py              # Custom logging utility
├── .env                              # Environment variables (local, ignored by Git)
├── .env.sample                       # Sample .env file for configuration
├── .gitignore                        # Specifies files/folders to ignore in Git
├── pytest.ini                        # Pytest configuration file
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies list
└──  tests/
│   ├── __init__.py
│   └── test_transactions_api.py             # Main API test suite
```

## Manually Triggering the CI Workflow (for Reviewers)
The Transaction Tests workflow (main.yml in .github/workflows/) is configured to run on workflow_dispatch (manual trigger).

1.  **Navigate to the GitHub repository:** 
2.  **Select the "Transaction Tests" workflow from the list.**
3.  **Click "Run workflow" on the right-hand side.**

Upon completion, the HTML test report will be available as a build artifact for download.

## Brief Report indicating the nature of issues with the API while building the tests
1.  **Currency is not getting displayed in the transactions for Customer 5.** 
2.  **Customer 3's purchase dates are not correctly displayed in descending order of dates.**
3.  **The date of transaction in customer 5's responses are not in the correct ISO8601 date format.**
4.  **Debit Amounts are not negative for certain transactions of Customer 5.**