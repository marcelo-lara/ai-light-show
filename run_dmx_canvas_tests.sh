#!/bin/bash

clear && cd /home/darkangel/ai-light-show 
python -m backend.tests.test_dmx_canvas

echo "--------------------------------------------"
echo "Running integration test with render engine:"
echo "--------------------------------------------"

python -m backend.tests.test_dmx_canvas_integration
