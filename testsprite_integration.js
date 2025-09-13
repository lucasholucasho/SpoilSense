// This script helps connect TestSprite with your Streamlit app

const { execSync } = require('child_process');
const fs = require('fs');

// Read TestSprite config
const config = JSON.parse(fs.readFileSync('.testsprite-config.json', 'utf8'));

// Start Streamlit app in background for testing
console.log('Starting Streamlit app for TestSprite testing...');
const streamlitProcess = require('child_process').spawn(
  'streamlit', ['run', 'streamlit_app.py'], 
  { detached: true, stdio: 'ignore' }
);

// Give Streamlit time to start
setTimeout(() => {
  console.log('Connecting to TestSprite...');
  try {
    // Use TestSprite MCP to run tests with API_KEY as environment variable
    execSync(`npx @testsprite/testsprite-mcp@latest --project=${config.projectName} --url=http://localhost:8501`, 
      { 
        stdio: 'inherit',
        env: { ...process.env, API_KEY: config.apiKey }
      }
    );
  } catch (error) {
    console.error('TestSprite execution failed:', error);
  } finally {
    // Cleanup: kill Streamlit process
    if (streamlitProcess && streamlitProcess.pid) {
      process.kill(-streamlitProcess.pid);
    }
  }
}, 5000);