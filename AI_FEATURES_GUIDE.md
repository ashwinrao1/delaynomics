# 🤖 AI Features Guide

This guide explains the new AI-powered features added to the Delaynomics dashboard.

## 🚀 Setup

### 1. Get Your Gemini API Key

1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the generated key

### 2. Configure Your API Key

Open the [.env](.env) file in the project root and replace `your-api-key-here` with your actual API key:

```bash
GEMINI_API_KEY=AIza...your-actual-key...
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Dashboard

```bash
python dashboard_app_premium.py
```

## ✨ New Features

### 1. 🤖 AI-Powered Insights Card

**What it does:**
- Automatically analyzes your airline performance data when the dashboard loads
- Generates 3 key insights:
  - Best performing airline and why
  - Worst performing airline and why
  - Surprising patterns or recommendations

**How it works:**
- Uses Google's Gemini Pro AI model
- Analyzes the top 5 best and worst 3 performers
- Provides data-driven insights with specific numbers

**Example insights:**
```
1. Best Performer: Alaska Airlines (AS) leads with $0.12 per mile,
   combining a low 23% delay rate with efficient operations.

2. Worst Performer: Spirit Airlines (NK) has the highest cost at $0.45
   per mile, driven by a 35% delay rate and 18-minute average delays.

3. Surprising Pattern: Southwest (WN) handles 3x more flights than
   competitors but maintains below-average delay costs - impressive scale.
```

### 2. 💬 Interactive AI Chatbot

**What it does:**
- Answers your questions about the flight delay data
- Provides personalized recommendations
- Explains trends and patterns

**How to use:**
1. Type your question in the text box
2. Click "Ask AI"
3. Get a data-driven answer in seconds

**Example questions:**
- "Which airline is best for cross-country flights?"
- "Why does JetBlue have higher delays?"
- "What time of week should I fly to avoid delays?"
- "Which airport has the worst delays?"
- "Compare Delta and United for reliability"

**How it works:**
- Sends your question + full dataset context to Gemini
- AI analyzes the data and formulates a specific answer
- Returns insights with actual numbers from your data

### 3. 📅 Day of Week Performance Chart

**What it shows:**
- Average delay rates by day of the week (Monday - Sunday)
- Average delay duration in minutes
- Helps you identify the best days to fly

**Key insights:**
- **Bar chart** (left axis): Shows what % of flights are delayed each day
- **Line chart** (right axis): Shows average delay duration in minutes
- **Color coding**: Red = worse delays, Green = better performance

**How to use:**
- Look for the lowest bars = best days to fly
- Compare weekdays vs weekends
- Plan your travel around low-delay days

## 🔒 Privacy & Security

- Your API key is stored in [.env](.env) which is in `.gitignore`
- Never commit your `.env` file to version control
- The AI only sees aggregated statistics, not individual flight records
- All API calls go directly to Google's servers (encrypted)

## ⚠️ Troubleshooting

### "AI Insights Unavailable" message

**Problem:** Dashboard shows warning that Gemini API is not configured

**Solutions:**
1. Check that [.env](.env) exists in the project root
2. Verify your API key is correct (no extra spaces)
3. Make sure `python-dotenv` is installed: `pip install python-dotenv`
4. Restart the dashboard after updating `.env`

### "Error generating insights" message

**Problem:** API call failed

**Possible causes:**
1. **Invalid API key** - Double-check your key at https://makersuite.google.com/app/apikey
2. **Rate limit exceeded** - Wait a minute and refresh
3. **Network issue** - Check your internet connection
4. **API quota exceeded** - Check your Google Cloud quota

### Chatbot not responding

**Problem:** Click "Ask AI" but nothing happens

**Solutions:**
1. Check browser console for errors (F12 → Console tab)
2. Verify you entered a question (not blank)
3. Check API key is configured correctly
4. Try a simpler question first

## 💡 Tips for Best Results

### Writing Good Questions

**Good questions:**
- ✅ "Which airline has the best on-time performance?"
- ✅ "Compare American Airlines and Delta for cost efficiency"
- ✅ "What's the worst airport for delays?"

**Poor questions:**
- ❌ "Tell me about planes" (too vague)
- ❌ "What's the weather like?" (not in the data)
- ❌ "Should I buy airline stocks?" (outside scope)

### Understanding the Insights

- **Carrier codes**: AA = American, DL = Delta, UA = United, WN = Southwest, etc.
- **Cost per mile**: Lower is better (more efficient)
- **Delay rate**: Percentage of flights delayed >15 minutes
- **Avg delay cost**: Economic impact using FAA's $74/minute estimate

## 📊 Data Context

The AI has access to:
- Airline performance metrics (15 carriers)
- Airport delay statistics (top 10 worst)
- Day-of-week patterns
- Cost efficiency calculations
- Delay rate percentages
- Flight volume data

The AI does NOT have:
- Real-time flight status
- Future predictions beyond patterns
- Weather data
- Ticket prices
- Individual flight details

## 🎯 Use Cases

### For Travelers
- "Which airline should I choose for reliability?"
- "What day of the week has fewer delays?"
- "Is it worth paying more for Delta vs Spirit?"

### For Business Analysts
- "Which carrier has the most consistent performance?"
- "What's the economic impact of delays at JFK?"
- "Compare low-cost carriers to legacy airlines"

### For Researchers
- "What patterns exist in weekend vs weekday delays?"
- "How does flight volume correlate with delays?"
- "Which airline handles high volume best?"

## 🔮 Future Enhancements

Potential additions (not yet implemented):
- Route-specific recommendations
- Seasonal trend analysis
- Airport-to-airport best carrier suggestions
- Delay prediction models
- Cost-benefit analysis for different booking strategies

---

**Need help?** Check the main [README.md](README.md) or open an issue on GitHub.
