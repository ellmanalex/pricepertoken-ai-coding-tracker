# AI Usage Tracker

Track and analyze your AI usage from Cursor IDE and Claude Code with detailed analytics and cost monitoring.

## 🚀 Quick Start

### Installation

```bash
npm install -g ai-usage-tracker
```

### Setup

1. **Register for an account** at [https://your-django-app.com/register/](https://your-django-app.com/register/)

2. **Get your API token** from [https://your-django-app.com/dashboard/](https://your-django-app.com/dashboard/)

3. **Configure the CLI**:
   ```bash
   ai-usage-tracker --configure YOUR_API_TOKEN
   ```

4. **Start tracking**:
   ```bash
   ai-usage-tracker --collect both
   ```

## 📊 Usage

### Local Mode (No Account Required)

View your usage data locally without sending it anywhere:

```bash
# View Cursor usage
ai-usage-tracker --local cursor

# View Claude usage  
ai-usage-tracker --local claude

# View both tools
ai-usage-tracker --local both
```

### Dashboard Mode (Account Required)

Send your usage data to your personal dashboard:

```bash
# Send Cursor data
ai-usage-tracker --collect cursor

# Send Claude data
ai-usage-tracker --collect claude

# Send both tools data
ai-usage-tracker --collect both
```

### Generate Reports

Create detailed usage reports saved to your local machine:

```bash
ai-usage-tracker --report
```

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `--local <tool>` | View usage locally (cursor, claude, both) |
| `--collect <tool>` | Send usage to dashboard (cursor, claude, both) |
| `--report` | Generate comprehensive usage report |
| `--configure <token>` | Set up your API token |
| `--help` | Show all available options |

## 📈 What It Tracks

### Cursor IDE
- Token usage by model (GPT-4, Claude, etc.)
- Request counts and costs
- Cache hit rates
- Usage over time

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

1. Check your token at [https://your-django-app.com/dashboard/](https://your-django-app.com/dashboard/)
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

- **Dashboard**: [https://your-django-app.com/](https://your-django-app.com/)
- **GitHub**: [https://github.com/yourusername/ai-usage-tracker](https://github.com/yourusername/ai-usage-tracker)
- **Issues**: [https://github.com/yourusername/ai-usage-tracker/issues](https://github.com/yourusername/ai-usage-tracker/issues)

---

**Made with ❤️ for the AI development community**