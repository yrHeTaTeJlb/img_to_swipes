#!/usr/bin/env sh
NODE_PATH="$(node -p 'require("path").dirname(process.execPath)')"
node "$NODE_PATH/node_modules/npm/bin/npm-cli.js" "$@"