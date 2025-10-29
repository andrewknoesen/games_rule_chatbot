#!/bin/bash/

kubectl get secret -n game-rules-chatbot | grep basic-auth

# Get credentials
kubectl get secret game-rules-chatbot-postgres-app  -n game-rules-chatbot -o jsonpath='{.data.username}' | base64 -d
kubectl get secret game-rules-chatbot-postgres-app  -n game-rules-chatbot -o jsonpath='{.data.password}' | base64 -d

