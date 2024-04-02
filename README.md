Encrypted files are stored locally in foo.txt

File permission data is stored in permissions.json. This file is encrypted and stored locally.

We also store hashed user password in the top level of permissions.json.

## How to run

1. Clone the repository
1. Add a local file fernet.key with the key used to encrypt the files
1. Create a directory called `files` in the root directory
1. Run `docker compose run app` in the root directory
