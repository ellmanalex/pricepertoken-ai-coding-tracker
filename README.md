# AI Usage Tracker

Track and analyze your AI usage from Cursor IDE and Claude Code with detailed analytics and cost monitoring.

## 🚀 Quick Start

### Installation

```bash
npm install -g ai-usage-tracker
```

### Setup

1. **Try local mode first** (no account required):
   ```bash
   ai-usage-tracker --local
   ```

2. **For dashboard mode** (account required):
   - Register at [https://pricepertoken.com/coding-tracker/]
   - Get your API token from the dashboard
   - Configure: `ai-usage-tracker --configure YOUR_API_TOKEN`
   - Run: `ai-usage-tracker --live`

## 📊 Usage

### Local Mode (No Account Required)

View your usage data locally without sending it anywhere:

```bash
# Monitor both Cursor and Claude usage locally
ai-usage-tracker --local
```

This will continuously monitor your usage and display summaries locally.

### Dashboard Mode (Account Required)

Send your usage data to your personal dashboard:

```bash
# Monitor and send data to dashboard
ai-usage-tracker --live
```

This will continuously monitor your usage and send data to your dashboard.

### Configuration

Set up your API token for dashboard mode:

```bash
# Save your API token
ai-usage-tracker --configure YOUR_API_TOKEN
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
export DJANGO_API_URL="https://your-custom-domain.com"

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

If you see dependency errors:

```bash
pip install -r requirements.txt
```

### Permission Issues

On macOS/Linux, you might need to run:

```bash
sudo npm install -g ai-usage-tracker
```

### API Token Issues

If you get authentication errors:

1. Check your token at [https://pricepertoken.com/coding-tracker/]
2. Reconfigure: `ai-usage-tracker --configure NEW_TOKEN`

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
- **GitHub**: [https://github.com/yourusername/ai-usage-tracker](https://github.com/yourusername/ai-usage-tracker)
- **Issues**: [https://github.com/yourusername/ai-usage-tracker/issues](https://github.com/yourusername/ai-usage-tracker/issues)

---

**Made with ❤️ for the AI development community**