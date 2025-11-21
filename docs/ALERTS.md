**SCNMS Alerting and Notification Guide**

This document explains how to enable Prometheus alerting rules and Grafana notification provisioning for SCNMS.

- Prometheus rules are located under `config/prometheus/rules/*.yml`.
- Grafana notifier provisioning files are under `config/grafana/provisioning/notifiers/`.

Quick start
1. Ensure Prometheus is configured to read rule files. The repository `config/prometheus.yml` now includes `rule_files: - "rules/*.yml"` which expects the container to mount `config/prometheus` into Prometheus' config directory.

2. If you're using `docker-compose.yml`, update the Prometheus service to mount the local config directory. Example snippet for the `prometheus` service:

```bash
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./config/prometheus/rules:/etc/prometheus/rules:ro
```

3. Restart Prometheus to load rules:

```bash
docker-compose restart prometheus
```

4. Configure the Grafana Slack webhook as an environment variable so the notifier provisioning can use it. For example, in the Grafana Docker service set `SLACK_WEBHOOK_URL`.

5. Restart Grafana to apply provisioning:

```bash
docker-compose restart grafana
```

Testing alerts
- Trigger a test critical alarm (or insert alarms into the DB) and verify Prometheus shows firing alerts at `http://localhost:9090/alerts`.
- Verify Grafana notification channels under Configuration → Notification channels.

Files added:
- `config/prometheus/rules/scnms_alerts.yml` — alert rules for SCNMS
- `config/grafana/provisioning/notifiers/slack.yml` — Grafana notifier provisioning template
