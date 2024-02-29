#!/bin/bash

# Start the Python script in the background and redirect output to logs
python v20.7.py > output.log 2> error.log &

echo "Program started."
