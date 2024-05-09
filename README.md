# telegram-gitlab-integration
Telegram bot checking pipeline status of MRs in gitlab ci

# Run via docker compose

Just run:
```bash
docker compose --verbose up
```

Run as daemon:
```bash
docker compose up -d
```

Stop daemon:
```bash
docker compose down -v
```

# Build and push

```bash
docker login -u <user> -p <pass>
docker buildx build --platform=linux/amd64 -t docker.io/<user>/tggl:0.0.1 --push  -f ./Dockerfile .
```

# Run in k8s

Create secrets file from template
```bash
cp k8s/secret-template.yaml k8s/secret.yaml
```

Fill envs and secrets
```bash
nano k8s/secret.yaml
```
or
```bash
vim k8s/secret.yaml
```

Deploy
```bash 
cd k8s
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
```
