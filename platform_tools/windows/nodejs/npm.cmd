@echo off
for /f "tokens=*" %%i in ('node -p "require(\"path\").dirname(process.execPath)"') do set NODE_PATH=%%i
node "%NODE_PATH%\node_modules\npm\bin\npm-cli.js" %*
