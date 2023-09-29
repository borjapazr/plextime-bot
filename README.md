# 🤖⏰ Plextime Bot

![GitHub CI Workflow Status](https://img.shields.io/github/actions/workflow/status/borjapazr/plextime-bot/ci.yml?branch=main&style=flat-square&logo=github&label=CI)

Plextime Bot is an automatic check-in and check-out tool for the Plextime platform. It's written in
[Python](https://www.python.org/) and scheduled using
[schedule](https://github.com/dbader/schedule).

## 🧩 Requirements

- [Python](https://www.python.org/)
- [Poetry](https://python-poetry.org/)
- [Docker](https://docs.docker.com/get-docker/) and
  [Docker Compose](https://docs.docker.com/compose/install/)
- [Make](https://www.gnu.org/software/make/)

## 🧑‍🍳 Configuration

Before deploying the service, it needs to be configured. To do so, create an `.env` file with the
content from the corresponding `.env.template`. Alternatively, you can use the `make env` command.

### Environment Variables

| Variable                           | Description                                                             | Example                                          | Default | Possible Values                                                  |
| ---------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------ | ------- | ---------------------------------------------------------------- |
| `PLEXTIME_TIMEZONE`                | Timezone for Plextime checks.                                           | `Europe/Madrid`                                  | `UTC`   | Timezone strings                                                 |
| `PLEXTIME_USER`                    | Plextime user.                                                          | janedoe                                          | `None`  | String values                                                    |
| `PLEXTIME_PASSWORD`                | Plextime user's password.                                               | password                                         | `None`  | String values                                                    |
| `PLEXTIME_CHECKIN_JOURNAL_OPTION`  | Type of check-in to be performed.                                       | `8`                                              | `8`     | `8` - Remote, `9` - Office, `10` - Client and `11` - Coffe break |
| `PLEXTIME_CHECKOUT_JOURNAL_OPTION` | Type of check-out to be performed.                                      | `8`                                              | `8`     | `8` - Remote, `9` - Office, `10` - Client and `11` - Coffe break |
| `PLEXTIME_ORIGIN`                  | Origin of Plextime checks.                                              | `2`                                              | `2`     | `1` - Mobile, `2` - Web                                          |
| `PLEXTIME_CHECKIN_RANDOM_MARGIN`   | Max value (in seconds) for the random timeout during check-in process.  | `900`                                            | `0`     | Numeric values                                                   |
| `PLEXTIME_CHECKOUT_RANDOM_MARGIN`  | Max value (in seconds) for the random timeout during check-out process. | `1800`                                           | `0`     | Numeric values                                                   |
| `PLEXTIME_TELEGRAM_NOTIFICATIONS`  | Enable or disable Telegram notifications.                               | `true`/`false`                                   | `false` | `true`, `false`                                                  |
| `PLEXTIME_TELEGRAM_BOT_TOKEN`      | Telegram bot token for notifications.                                   | `1650167098:AAHrNOdsp6RUDd-kkKbB9eYGif-wkOOcGAQ` | `None`  | String values                                                    |
| `PLEXTIME_TELEGRAM_CHANNEL_ID`     | Telegram channel for notifications.                                     | `5192286`                                        | `None`  | Numeric or String channel IDs                                    |

## 🏗️ Installation

- Install dependencies:

  ```bash
  make install
  ```

- Run the application locally:

  ```bash
  make start
  ```

- Run the application with Docker:

  ```bash
  make start/docker
  ```

- Stop the application running in a Docker container:

  ```bash
  make stop/docker
  ```

- Show logs of the application running in a Docker container:

  ```bash
  make logs
  ```

## 🧙 Usage

```bash
Usage: make TARGET [ARGUMENTS]

Targets:
  build                     Build wheel file using poetry
  dependencies              Check Poetry lock file consistency and for obsolete dependencies
  env                       Create .env file from .env.template
  format                    Run code formatting
  help                      Show this help
  install                   Install the poetry environment and install the pre-commit hooks
  lint                      Run code linting
  logs                      Show logs for all or c=<name> containers
  requirements              Check if requirements are satisfied
  start                     Start the service
  start/docker              Start the service in a Docker container
  stop/docker               Stop the service running in a Docker container
  test                      Test code with PyTest
  types                     Run type checks
```

## ⚖️ License

The MIT License (MIT). Please see [License](LICENSE) for more information.
