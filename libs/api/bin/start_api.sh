#!/bin/bash

set -e

basepath=$(dirname "$0")
cd "$basepath/../src"
uvicorn rules_api.main:app
