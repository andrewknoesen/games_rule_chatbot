#!/bin/bash

set -e

basepath=$(dirname "$0")
cd "$basepath/../"
uvicorn main:app
