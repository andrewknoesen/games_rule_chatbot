#!/bin/bash

set -e

basepath=$(dirname "$0")
cd "$basepath/../"

set -a
source .env
set +a

uvicorn main:app
