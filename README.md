# Get all Gmail messages and aggregate them

## Setup

Prepare the GCP environment and obtain credentials.

- https://developers.google.com/gmail/api/quickstart/python

Install libraries.

- `$ pip install -r requirements.txt`


If you see an `invalid_grant` error, the refresh token may be outdated. Please delete `token.json` and run `quickstart.py` again.

## Usage

`$ python main.py <your Gmail address.>`
