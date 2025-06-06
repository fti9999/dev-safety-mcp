"""
Real project integration tests for Development Safety MCP Server

Tests the MCP server with realistic project scenarios.
"""

import pytest
import asyncio
import tempfile
import os
import shutil
import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import DevSafetyMCP


class TestRealProjectIntegration:
    """Test with realistic project scenarios"""
    
    def setup_method(self):
        """Set up test environment with a realistic project"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a realistic React project structure
        self.project_path = os.path.join(self.temp_dir, "my_react_app")
        self.create_realistic_project()
        
        self.server = DevSafetyMCP()
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_realistic_project(self):
        """Create a realistic project structure for testing"""
        project = Path(self.project_path)
        project.mkdir(parents=True)
        
        # package.json
        package_json = {
            "name": "my-react-app",
            "version": "0.1.0",
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test"
            }
        }
        
        with open(project / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # src directory with components
        src_dir = project / "src"
        src_dir.mkdir()
        
        # App.js
        with open(src_dir / "App.js", "w") as f:
            f.write("""
import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>My React App</h1>
      </header>
    </div>
  );
}

export default App;
""")
        
        # App.css
        with open(src_dir / "App.css", "w") as f:
            f.write("""
.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
}
""")
        
        # components directory
        components_dir = src_dir / "components"
        components_dir.mkdir()
        
        # Header component
        with open(components_dir / "Header.jsx", "w") as f:
            f.write("""
import React from 'react';

const Header = ({ title }) => {
  return (
    <header>
      <h1>{title}</h1>
    </header>
  );
};

export default Header;
""")
        
        # README.md
        with open(project / "README.md", "w") as f:
            f.write("""
# My React App

A sample React application for testing the Development Safety MCP Server.

## Features

- React components
- CSS styling
- Modern JavaScript

## Getting Started

1. Install dependencies: `npm install`
2. Start development server: `npm start`
3. Build for production: `npm run build`
""")
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete development workflow"""
        # Step 1: Create sandbox
        result = await self.create_sandbox_tool()
        assert result["status"] == "created"
        sandbox_path = result["sandbox_path"]
        
        # Verify sandbox exists and has files
        assert os.path.exists(sandbox_path)
        assert os.path.exists(os.path.join(sandbox_path, "package.json"))
        assert os.path.exists(os.path.join(sandbox_path, "src", "App.js"))
        
        # Step 2: Save session state
        session_result = await self.save_session_tool(sandbox_path)
        assert session_result["status"] == "saved"
        
        # Step 3: Load session state
        load_result = await self.load_session_tool()
        assert load_result["status"] == "loaded"
        assert "continuation_prompt" in load_result
        
        # Step 4: Check activity
        activity_result = await self.check_activity_tool(sandbox_path)
        assert activity_result["status"] == "success"
        
        # Step 5: Sync changes (simulate some changes first)
        self.simulate_changes(sandbox_path)
        sync_result = await self.sync_to_main_tool(sandbox_path)
        assert sync_result["status"] == "synced"
    
    async def create_sandbox_tool(self):
        """Helper to call create_sandbox tool"""
        # Simulate calling the MCP tool
        tools = self.server.server._tools
        create_tool = tools["create_sandbox"]
        return await create_tool(self.project_path)
    
    async def save_session_tool(self, sandbox_path):
        """Helper to call save_session_state tool"""
        tools = self.server.server._tools
        save_tool = tools["save_session_state"]
        return await save_tool(
            operation="Add payment feature",
            current_step="Created sandbox and initial setup",
            next_steps=["Add payment component", "Integrate with API", "Add tests"],
            sandbox_path=sandbox_path,
            context={"feature": "payment", "priority": "high", "estimate": "2 days"}
        )    
    async def load_session_tool(self):
        """Helper to call load_session_state tool"""
        tools = self.server.server._tools
        load_tool = tools["load_session_state"]
        return await load_tool()
    
    async def check_activity_tool(self, sandbox_path):
        """Helper to call check_activity tool"""
        tools = self.server.server._tools
        activity_tool = tools["check_activity"]
        return await activity_tool(sandbox_path, minutes=10)
    
    async def sync_to_main_tool(self, sandbox_path):
        """Helper to call sync_to_main tool"""
        tools = self.server.server._tools
        sync_tool = tools["sync_to_main"]
        return await sync_tool(sandbox_path, self.project_path)
    
    def simulate_changes(self, sandbox_path):
        """Simulate some file changes in the sandbox"""
        # Add a new component
        new_component_path = os.path.join(sandbox_path, "src", "components", "Payment.jsx")
        with open(new_component_path, "w") as f:
            f.write("""
import React, { useState } from 'react';

const Payment = () => {
  const [amount, setAmount] = useState('');
  
  const handlePayment = () => {
    console.log('Processing payment for:', amount);
  };
  
  return (
    <div className="payment">
      <h2>Payment</h2>
      <input 
        type="number" 
        value={amount} 
        onChange={(e) => setAmount(e.target.value)}
        placeholder="Enter amount"
      />
      <button onClick={handlePayment}>Pay Now</button>
    </div>
  );
};

export default Payment;
""")
        
        # Update App.js to include the new component
        app_js_path = os.path.join(sandbox_path, "src", "App.js")
        with open(app_js_path, "w") as f:
            f.write("""
import React from 'react';
import './App.css';
import Payment from './components/Payment';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>My React App</h1>
      </header>
      <main>
        <Payment />
      </main>
    </div>
  );
}

export default App;
""")


if __name__ == "__main__":
    pytest.main([__file__])