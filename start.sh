#!/bin/bash

OPTS=${1:---host 0.0.0.0 --port 8050}

source ./env/bin/activate
flask run $OPTS
