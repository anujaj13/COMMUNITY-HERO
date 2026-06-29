#!/bin/sh

# If API_BASE_URL is set, replace the default localhost:8000 in index.html
if [ -n "$API_BASE_URL" ]; then
    echo "Configuring API_BASE_URL to $API_BASE_URL"
    # Replace the window.API_BASE_URL assignment in index.html
    sed -i "s|window.API_BASE_URL = 'http://localhost:8000';|window.API_BASE_URL = '$API_BASE_URL';|g" /app/index.html
else
    echo "Using default API_BASE_URL: http://localhost:8000"
fi

# Execute the command passed to the docker container
exec "$@"
