#!/bin/bash
SASS_CMD="sass"
POSTCSS_CMD="postcss"

if ! [ -x "$(command -v sass)" ]; then
  SASS_CMD="npx --no-install sass"
fi

if ! [ -x "$(command -v postcss)" ]; then
  POSTCSS_CMD="npx --no-install postcss"
fi

FILES=(sass_processed/style.css sass_processed/content-description.css sass_processed/table.css sass_processed/ranks.css)

cd `dirname $0`
$SASS_CMD --silence-deprecation=import resources:sass_processed

echo
$POSTCSS_CMD "${FILES[@]}" --verbose --use autoprefixer -d resources

