# Gmail Automation Script

## Overview

This project is a standalone Python script that integrates with the Gmail API to fetch emails, store them in a relational database, and apply rule-based operations on them.

## Features

- Authenticate with the Gmail API using OAuth.
- Fetch and store emails in a relational database (SQLite3).
- Process emails based on user-defined rules stored in a JSON file.
- Perform actions like marking emails as read/unread and moving messages.

## Installation

1. **Clone the Repository**
  ```bash
  git clone https://github.com/AgPriyanshu/gmail-actions.git
  cd gmail-actions
  ```

## Running the Script

1. **Install the Required Packages**
  ```bash
  pip install -r requirements.txt
  ```

2. **Run the Script**
  ```bash
  python -m app.email_processor --mode <mode>
  ```

  Replace `<mode>` with one of the following options:
  - `fetch`: To fetch emails from Gmail and store them in the database.
  - `process`: To process emails based on user-defined rules.
  - `display`: To display emails stored in the database.

  Example:
  ```bash
  python -m app.email_processor --mode fetch
  ```

3. **Running Tests**

  To run the test suite using pytest, use the following command:
  ```bash
  pytest ./app/tests
  ```

This will automatically discover and run all test files inside the tests/ directory.

## References

For more detailed information, please refer to the [REFERENCES.md](REFERENCES.md) file.
