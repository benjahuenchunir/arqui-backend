# 2024-1 / IIC2173 - E0 | CoolGoat Async

## Accessing the backend (protected by API Gateway)
- [numby.me](https://api.numby.me)

_"...the Warp Trotter "[Numby](https://honkai-star-rail.fandom.com/wiki/Topaz_and_Numby)," is also capable of acutely perceiving where "riches" are located. It can even perform jobs involving security, debt collection, and actuarial sciences."_


## Table of Contents

- [Installation](#installation)
- [Structure](#structure)
- [Dependencies](#dependencies)
- [CI Pipeline](#ci-pipeline)
- [Local Development](#local-development)

## Installation

To get started, clone the repository and install the dependencies:

```sh
git clone https://github.com/benjahuenchunir/arqui-backend.git
cd arqui-backend
```

## Structure

`API`: Main api used for storing and handling requests
`listener`: Subscribes to broker on all channels and communicates with the API
`publisher`: Used for publishing in the broker

## Dependencies

Each component has a requirements folder with common, development and production dependencies.

## CI Pipeline
The CI pipeline is set up using GitHub Actions. It includes steps for building Docker images, running tests, and deploying to an EC2 instance.

It is separated into two jobs, both using the environment `build_test_env` and secrets.

### On pull requests to `main` run Build Job
1. **Checkout Code:** Uses the `actions/checkout@v3` action to check out the repository code.
2. **Set Up Docker:** Uses the `docker/setup-buildx-action@v2` action to set up Docker Buildx.
3. **Install Docker Compose:** Downloads and installs Docker Compose.
4. **Build Docker Images:** Runs `docker-compose build` to build the Docker images.
5. **Run Docker Containers:** Runs `docker-compose up -d` to start the Docker containers with the necessary environment variables.
6. **Install Python:** Installs Python 3 and pip.
7. **Install Requests Library:** Installs the `requests` library using pip.
8. **Wait for Containers to Start:** Waits for 20 seconds to ensure the containers are up and running.
9. **Run API Tests:** Runs `python3 test_services.py` to execute the API tests (are services running and does root redirection work).
10. **Check Listener Logs:** Checks the logs of the `arquisis-listener` container to ensure it connected to the broker.
11. **Stop Containers:** Runs `docker-compose down` to stop the Docker containers.

### On push to `main` run Deploy Job
1. **Run Build Job:** Executes the Build Job and, if successful, continues to the next steps.
2. **Checkout Code:** Uses the `actions/checkout@v3` action to check out the repository code.
3. **Deploy to EC2:** Uses the `appleboy/ssh-action@master` action to SSH into the EC2 instance and deploy the latest code:
   - Navigates to the `arqui-backend` directory.
   - Pulls the latest code from the `main` branch.
   - Stops any running Docker containers.
   - Builds and starts the Docker containers using `docker-compose up --build -d`.

### Setting Up Secrets and Enviroment
To set up the necessary secrets for AWS credentials and CloudFront distribution ID:

#### Secrets
1. Go to your GitHub repository.
2. Click on Settings.
3. Click on Secrets in the left sidebar.
4. Click on New repository secret.
5. Add the following secrets: 
  - `EC2_HOST` The hostname or IP address of your EC2 instance
  - `EC2_PRIVATE_KEY` The private key used to SSH into your EC2 instance
  - `EC2_USER` The username used to SSH into your EC2 instance

#### Env Secrets
1. Go to your GitHub repository.
2. Click on Settings.
3. Click on Environments in the left sidebar.
4. Create a new environment called production
5. Add the following secrets: 
  - `MQTT_HOST` The hostname of your MQTT broker
  - `MQTT_PASSWORD` The password for your MQTT broker
  - `MQTT_PORT` The port number of your MQTT broker
  - `MQTT_USER` The username for your MQTT broker

#### Env
1. Go to your GitHub repository.
2. Click on Settings.
3. Click on Environments in the left sidebar.
4. Create a new environment called production
5. Add the following variables: 
  - `GROUP_ID` The group ID for your application
  - `PATH_FIXTURES` The path to your fixtures endpoint
  - `PATH_REQUESTS` The path to your requests endpoint
  - `POSTGRES_DB_NAME` The name of your PostgreSQL database
  - `POSTGRES_PASSWORD` The password for your PostgreSQL database
  - `POSTGRES_USER` The username for your PostgreSQL database
  - `POST_TOKEN` The token used for posting data

## Local development

To run locally, add every secret and environment variable to a `.env` file.
A template `.env.example` is provided.

You need to fill in the following variables in your `.env` file:

- `API_HOST` The hostname for your API server (e.g., `localhost`)
- `API_PORT` The port number for your API server (e.g., `8000`)
- `DATABASE_URL` The URL for your database connection (e.g., `sqlite:///test.db` for SQLite or `postgresql://user:password@localhost/dbname` for PostgreSQL)
- `PUBLISHER_HOST` The hostname for your publisher service (e.g., `localhost`)
- `PUBLISHER_PORT` The port number for your publisher service (e.g., `7999`)
- `ENV` Enviroment to run (e.g., `development`)

# Instalations and AWS nginx Setup

## Instalar Docker Compose

```sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Para revisar si se instaló bien

```sh
docker-compose --version
```

## Construir imagenes con Docker Compose

Para construir y levantar la base de datos, api y listener del broker ejecutar el siguiente comando en el mismo directorio que el archivo `docker-compose.yaml`
```sh
docker-compose up --build
```

Si se agrega `-d` se corre en background

## Nginx

### Instalar NGINX
```sh
  sudo apt update
  sudo apt install nginx
```

### Configurar NGINX

Necesitas desvincular la página predeterminada para poder cambiar la configuración predeterminada:
```sh
  sudo unlink /etc/nginx/sites-enabled/default
```

Luego necesitas escribir tu propio archivo de configuración o usar el archivo `api.conf` proporcionado.

Para copiar el `api.conf` proporcionado a `/etc/nginx/sites-enabled/`.
```sh
sudo cp ./api.conf /etc/nginx/sites-enabled/
```

Para crear un nuevo `api.conf` en el directorio
```sh
sudo touch ./api.conf /etc/nginx/sites-enabled/api.conf
```

Para editar el `api.conf`

```sh
sudo nano ./api.conf /etc/nginx/sites-enabled/api.conf
```

Finalmente, puedes probar nginx y reiniciarlo cuando no muestre errores.
```sh
sudo nginx -t
sudo systemctl restart nginx
```

## SSL Certificate
Seguir instrucciones de [https://certbot.eff.org/](https://certbot.eff.org/)

Para realizar el chequeo de expiración dos veces al día generar una tarea con crontab
```sh
sudo crontab -e
```

Agregar la siguiente tarea
```sh
0 0,12 * * * certbot renew --quiet
```