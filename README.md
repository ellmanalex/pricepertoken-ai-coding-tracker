# AI Usage Tracker

Track and analyze your AI usage from Cursor IDE and Claude Code with detailed analytics and cost monitoring.

## 🚀 Quick Start

### Installation

```bash
npm install -g ppt-tracker
```

**Note**: This package requires Python 3.8+ to be installed on your system. The installer will automatically install the required Python dependencies.

### Setup

1. **Try local mode first** (no account required):
   ```bash
   ppt-tracker --local
   ```

2. **For dashboard mode** (account required):
   - Register at [https://pricepertoken.com/coding-tracker/]
   - Get your API token from the dashboard
   - Configure: `ppt-tracker --configure YOUR_API_TOKEN`
   - Run: `ppt-tracker --live`

```

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `--local` | Monitor usage locally (no API calls) |
| `--live` | Monitor usage and send to dashboard |
| `--configure TOKEN` | Save API token for dashboard mode |
| `--help` | Show all available options |

## 📈 What It Tracks

### Cursor IDE
- Token usage by model (GPT-4, Claude, etc.)
- Request counts and costs
- Cache hit rates
- Usage over time
- Kind of requests (chat, completion, etc.)
- Subscription vs paid usage

### Claude Code
- Token consumption
- Model usage breakdown
- Daily/monthly summaries
- Cost analysis

## 🔒 Privacy

- **Local Mode**: Your data never leaves your machine
- **Dashboard Mode**: Data is sent securely to your personal dashboard
- **Open Source**: Full transparency - inspect the code yourself
- **Your Control**: Revoke access anytime from your dashboard

## 🔧 Configuration

### Environment Variables

```bash
# Set custom Django server URL
export DJANGO_API_URL="https://api.pricepertoken.com"

# Set API token (alternative to --configure)
export AI_USAGE_TRACKER_TOKEN="your_token_here"
```

### Config File

The CLI stores your configuration in `~/.ai-usage-tracker/config`

## 📋 Requirements

- **Python 3.8+** (automatically checked during installation)
- **Node.js 14+** (for npm installation)
- **Cursor IDE** (for Cursor usage tracking)
- **Claude Code CLI** (for Claude usage tracking)

## 🐛 Troubleshooting

### Python Dependencies

If you see dependency errors like "No module named 'httpx'":

```bash
# Install required Python packages
pip install httpx==0.25.2 PyJWT==2.8.0

# Or reinstall the npm package to trigger dependency installation
npm install -g ppt-tracker
```

### Python Not Found

If Python is not found:

1. Install Python 3.8+ from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Make sure `python3` or `python` is in your PATH
3. Reinstall the npm package: `npm install -g ppt-tracker`

### Permission Issues

On macOS/Linux, you might need to run:

```bash
sudo npm install -g ppt-tracker
```

### API Token Issues

If you get authentication errors:

1. Check your token at [https://pricepertoken.com/coding-tracker/]
2. Reconfigure: `ppt-tracker --configure NEW_TOKEN`

### Rate Limits

If you hit rate limits:

- Wait a few minutes before trying again
- Use `--local` mode to view data without API calls
- Check your usage limits in the dashboard

## 🤝 Contributing

This is an open-source project! Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- **Dashboard**: [https://pricepertoken.com/coding-tracker/](https://pricepertoken.com/coding-tracker/)
- **GitHub**: [https://github.com/ellmanalex/pricepertoken-ai-coding-tracker](https://github.com/ellmanalex/pricepertoken-ai-coding-tracker)
- **Issues**: [https://github.com/ellmanalex/pricepertoken-ai-coding-tracker/issues](https://github.com/ellmanalex/pricepertoken-ai-coding-tracker/issues)

---

**Made with ❤️ for the AI development community**