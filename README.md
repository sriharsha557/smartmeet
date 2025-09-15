# SmartMeet AI - Intelligent Meeting Scheduler

SmartMeet AI is an intelligent meeting scheduling application that uses AI to analyze participant availability and suggest optimal meeting times. It integrates with Microsoft 365 calendars and provides a user-friendly Streamlit interface.

## Features

- 🤖 **AI-Powered Scheduling**: Uses OpenAI and LangChain to intelligently suggest meeting times
- 📅 **Microsoft 365 Integration**: Connects to Microsoft Graph API for calendar access
- 💬 **Natural Language Processing**: Chat with the AI assistant using natural language
- 📊 **Dashboard & Analytics**: View meeting trends and statistics
- 📧 **Automatic Notifications**: Send meeting invitations and reminders
- ⚡ **Conflict Resolution**: Automatically detect and resolve scheduling conflicts

## Project Structure

```
SmartMeet/
├── Main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
├── agents/                # AI agents for different tasks
│   ├── __init__.py
│   ├── scheduler_agent.py  # Main scheduling AI agent
│   ├── calendar_agent.py   # Microsoft Graph calendar integration
│   └── notification_agent.py # Email notifications
├── services/              # Core services
│   ├── __init__.py
│   └── database.py        # SQLite database service
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── auth.py           # Microsoft OAuth authentication
│   └── date_utils.py     # Date and time utilities
└── data/                 # Database files (created automatically)
    └── meetings.db
```

## Installation

### 1. Clone or Download the Project

Make sure all files are in the correct directory structure as shown above.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID=your_client_id_here
MICROSOFT_CLIENT_SECRET=your_client_secret_here
MICROSOFT_TENANT_ID=your_tenant_id_or_common

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration (Optional)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

## Configuration Setup

### Microsoft Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in:
   - **Name**: SmartMeet AI
   - **Supported account types**: Accounts in any organizational directory and personal Microsoft accounts
   - **Redirect URI**: Web - `http://localhost:8501/auth/callback`
5. After creation, note down:
   - **Application (client) ID** → `MICROSOFT_CLIENT_ID`
   - **Directory (tenant) ID** → `MICROSOFT_TENANT_ID`
6. Go to "Certificates & secrets" > "New client secret"
   - Note down the secret value → `MICROSOFT_CLIENT_SECRET`
7. Go to "API permissions" > "Add a permission" > "Microsoft Graph" > "Delegated permissions"
   - Add: `Calendars.ReadWrite`, `User.Read`, `Mail.Send`
8. Click "Grant admin consent"

### OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up/Login
3. Go to "API Keys" section
4. Create a new API key
5. Copy the key → `OPENAI_API_KEY`

### Email Configuration (Optional)

For Gmail:
1. Enable 2-factor authentication
2. Generate an "App Password"
3. Use your Gmail address as `SMTP_USERNAME`
4. Use the app password as `SMTP_PASSWORD`

## Running the Application

```bash
streamlit run Main.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

### 1. Authentication
- Click "Connect to Microsoft 365" in the sidebar
- Complete the OAuth flow to connect your Microsoft account

### 2. Schedule a Meeting
- Go to "Schedule Meeting" page
- Fill in meeting details (title, participants, duration, etc.)
- Click "Find Smart Suggestions"
- Review AI-generated suggestions and select one

### 3. Chat Assistant
- Use the "Chat Assistant" page to interact with the AI
- Ask questions like:
  - "Schedule a team meeting for tomorrow at 2 PM"
  - "Check availability for john@company.com this week"
  - "Find a time for 5 people next Tuesday"

### 4. View Dashboard
- Monitor meeting statistics and trends
- See upcoming meetings and their status

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check that all files are in the correct directory structure

2. **Authentication Issues**
   - Verify your Microsoft App Registration settings
   - Check that redirect URI matches exactly: `http://localhost:8501/auth/callback`
   - Ensure API permissions are granted

3. **OpenAI API Errors**
   - Verify your API key is correct
   - Check you have sufficient credits/quota
   - Ensure the key has the necessary permissions

4. **Database Issues**
   - The SQLite database is created automatically in the `data/` folder
   - If you encounter issues, delete the `data/meetings.db` file to reset

### Development Mode

To run in development mode with more detailed logging:

```bash
export DEBUG=True
streamlit run Main.py
```

## Features in Detail

### AI Scheduling Agent
- Analyzes participant availability using Microsoft Graph API
- Considers meeting priority, duration, and preferences
- Generates confidence scores for each suggestion
- Provides human-readable reasoning for recommendations

### Calendar Integration
- Real-time availability checking
- Meeting creation and updates
- Conflict detection and resolution
- Support for recurring meetings

### Natural Language Processing
- Chat interface for scheduling requests
- Understands context and preferences
- Extracts meeting details from natural language
- Provides conversational responses

## Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Include docstrings for new functions
4. Test thoroughly before submitting changes

## License

This project is for internal use. Please ensure compliance with your organization's policies regarding AI and data usage.

## Support

For issues or questions:
1. Check this README first
2. Review the troubleshooting section
3. Check the application logs for error details
4. Contact the development team

---

**SmartMeet AI v1.0** - Making meeting scheduling intelligent and effortless! 🤖📅