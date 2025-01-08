#!/bin/bash
cd "$(dirname "$0")"/..

gdk component build
sudo /greengrass/v2/bin/greengrass-cli deployment create \
  --recipeDir $PWD/greengrass-build/recipes \
  --artifactDir $PWD/greengrass-build/artifacts \
  --merge "demoTiaToTimestream=1.0.0"