#!/bin/bash/

# Get all info at once
echo "Console IP: $(kubectl get svc game-rules-chatbot-minio-console -n game-rules-chatbot -o jsonpath='{.status.loadBalancer.ingress[0].ip}')" && \
echo "API IP: $(kubectl get svc minio -n game-rules-chatbot -o jsonpath='{.status.loadBalancer.ingress[0].ip}')" && \
echo "Credentials: $(kubectl get secret game-rules-chatbot-minio-creds -n game-rules-chatbot -o jsonpath='{.data.config\.env}' | base64 --decode)"
