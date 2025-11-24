# Managing Environment Variables

This project uses environment-specific `.env` files to manage configuration for different environments. The available environments are:

| Environment   | File          | Description                  |
|---------------|---------------|------------------------------|
| Local         | `local.env`   | For local development        |
| Dev           | `dev.env`     | For development environment  |
| Production    | `.env`        | For production environment   |

## Switching Environments

To load environment variables for a specific environment, run the corresponding command below in your shell. These commands source the appropriate `.env` file into your current shell session.

### General Command

Replace `<environment>` with `local` or `dev`:

```bash
set -o allexport && source <environment>.env && set +o allexport
```

### Specific Commands
#### Local Environment
```bash
set -o allexport && source local.env && set +o allexport
```
Dev Environment
```bash
set -o allexport && source dev.env && set +o allexport
```
Production Environment
```bash
set -o allexport && source .env && set +o allexport
```

These commands temporarily enable allexport (so all variables defined in the file are exported), source the environment file, then disable allexport again.
