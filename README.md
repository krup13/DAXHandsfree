# DAX Handsfree Driver Assistant

A voice-enabled assistant for Grab drivers with real-time navigation, earnings tracking, and ride management.

## Features

- Voice-enabled AI assistant with natural language understanding
- Real-time navigation with busy area detection
- Earnings tracking and customer history
- Driver profile management
- Ride request management with voice notifications
- Multi-page interface for easy access to all features

## Setup

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- Google Maps API key
- Google AI API key
- DialogFlow project setup

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DAXHandsfree.git
cd DAXHandsfree
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Environment Variables Setup

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit `.env` and add your API keys:
```
GOOGLE_AI_API_KEY="your_google_ai_api_key_here"
GOOGLE_MAPS_API_KEY="your_google_maps_api_key_here"
DIALOGFLOW_PROJECT_ID="your_dialogflow_project_id_here"
GOOGLE_APPLICATION_CREDENTIALS="path_to_your_credentials.json"
```

### Getting API Keys

1. Google Maps API Key:
   - Visit the [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the following APIs:
     * Maps JavaScript API
     * Places API
     * Directions API
     * Distance Matrix API
   - Create credentials (API key)
   - Add restrictions to the API key for security

2. Google AI API Key:
   - Visit the [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key to your `.env` file

3. DialogFlow Setup:
   - Visit the [DialogFlow Console](https://dialogflow.cloud.google.com)
   - Create a new agent
   - Download the credentials JSON file
   - Move the file to your project directory
   - Update the GOOGLE_APPLICATION_CREDENTIALS path in `.env`

### Security Notes

- Never commit the `.env` file or any credentials to version control
- The `.gitignore` file is configured to prevent accidental commits of sensitive files
- Always use environment variables for secrets in production
- Regularly rotate API keys and monitor usage
- Add IP restrictions and other security measures to your API keys in the respective consoles

## Running the Application

1. Ensure your virtual environment is activated
2. Start the application:
```bash
python app.py
```
3. Open a web browser and navigate to:
```
http://localhost:5000
```

## Development

- The application uses mock data when API keys are not available or invalid
- Check the console for any warnings or errors related to API keys
- Test all features with both real and mock data before deployment

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
