#!/bin/bash
echo "Enter your GitHub Personal Access Token:"
read -s GITHUB_TOKEN
echo ""
echo "Pushing to GitHub..."
git push https://${GITHUB_TOKEN}@github.com/Andrew-deb/stock-watchlist-app.git main
echo ""
echo "Done! Check https://github.com/Andrew-deb/stock-watchlist-app"
