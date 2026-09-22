# Modulo 09: Messa in produzione

> Stato: 🟡 scaletta (contenuti da scrivere)

## Obiettivi di apprendimento
Al termine del modulo lo studente sa:
- _(da definire)_

## Prerequisiti
- _(da definire)_

## Argomenti
1. Server come servizio: systemd, Docker Compose
2. Reverse proxy con HTTPS (es. Caddy) e autenticazione
3. Monitoraggio: `/metrics` Prometheus, log, health check
4. Dimensionamento, code di richieste, limiti
5. Sicurezza: esposizione, prompt injection, modelli da fonti fidate
6. Aggiornamenti e rollback della versione di llama.cpp

## Laboratori
- [Il server come servizio](../../laboratori/lab-09-01-servizio/README.md): Installare il server come servizio systemd con riavvio automatico e log.
- [Proxy e monitoraggio](../../laboratori/lab-09-02-proxy-monitoraggio/README.md): Mettere il server dietro Caddy con chiave API e raccogliere le metriche con Prometheus/Grafana.

## Verifica
- Quiz di fine modulo: _(da scrivere)_

## Riferimenti
- Repository: https://github.com/ggml-org/llama.cpp
