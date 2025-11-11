#!/bin/bash

set -e

basepath=$(dirname "$0")
cd "$basepath/../src"
uvicorn games_rule_api.main:app
