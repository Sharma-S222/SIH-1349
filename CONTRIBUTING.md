# Git Workflow

## Branches

- **main** = stable/release branch
- **develop** = integration branch
- **feature/** = short-lived development branches
- **fix/** = bug fixes

## Workflow

1. Work on feature/fix branches off `develop`
2. Submit Pull Request to merge into `develop`
3. After testing, merge `develop` into `main` via release PR

## Contract Changes

- Contract changes must be reviewed by affected members
- Member 5 coordinates integration compatibility
- Never commit: `.env`, API keys, database passwords, private CCTV credentials, private RTSP URLs, model weights, large datasets, large generated videos, virtual environments, personal absolute paths

## Ownership

- Member 1: ai/detection/, ai/crowd/
- Member 2: ai/tracking/, ai/safety/
- Member 3: backend/
- Member 4: frontend/
- Member 5: integration/, deployment/runtime integration, environment standardization, performance, release integration
- Member 6: docs/testing/, docs/research/, demo/, quality documentation