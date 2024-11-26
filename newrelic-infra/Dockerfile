FROM newrelic/infrastructure:latest

# Instalar Tini usando apk
RUN apk add --no-cache tini

ADD newrelic-infra.yml /etc/newrelic-infra.yml

# Usa Tini como el proceso principal
ENTRYPOINT ["/sbin/tini", "--"]

# Comando por defecto del contenedor
CMD ["newrelic-infra"]