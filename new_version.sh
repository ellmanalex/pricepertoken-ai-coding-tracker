# 1. Clean up any cached files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 2. Remove any CSV files that shouldn't be in the package
rm -f cli_tool/*.csv

# 3. Commit all your changes
git add .
git commit -m "Update CLI with aggregation and simplified commands"

# 4. Update the package version
npm version patch

# 5. Publish the new version
npm publish --access public

# 6. Uninstall the old version
npm uninstall -g pricepertoken-ai-coding-tracker

# 7. Install the new version
npm install -g pricepertoken-ai-coding-tracker

# 8. Test the new version
pricepertoken-ai-coding-tracker --help