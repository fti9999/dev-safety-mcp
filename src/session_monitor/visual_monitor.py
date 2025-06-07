"""
Visual Session Monitor - Core Component

This module implements the core visual monitoring system that:
- Takes screenshots of LLM interfaces at intervals
- Analyzes screenshots to determine session state
- Takes appropriate actions based on analysis
- Integrates with multiple LLM platforms

Based on original handoff document Phase 2.1
"""

import asyncio
import time
import base64
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None
    print("Warning: pyautogui not installed - screenshot functionality disabled")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
    print("Warning: openai not installed - GPT-4V analysis disabled")

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
    print("Warning: anthropic not installed - Claude analysis disabled")


class VisualSessionMonitor:
    """
    Core visual monitoring system for LLM session state detection
    
    Implements the visual monitoring strategy from the original handoff document:
    - Continuous screenshot capture
    - AI-powered session state analysis
    - Automatic action based on session state
    - Interface-agnostic design
    """
    
    def __init__(self, interface_type: str, config: Dict[str, Any] = None):
        """
        Initialize visual session monitor
        
        Args:
            interface_type: Type of interface ("claude_desktop", "cursor", "vscode", "web_llm")
            config: Configuration options
        """
        self.interface_type = interface_type
        self.config = config or {}
        self.monitoring = False
        self.screenshot_dir = self._setup_screenshot_directory()
        
        # Initialize AI clients for screenshot analysis
        self.openai_client = None
        self.anthropic_client = None
        
        if OpenAI and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI()
            
        if Anthropic and os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = Anthropic()
        
        # Session state tracking
        self.last_analysis = None
        self.state_history = []
        self.action_log = []
        
        print(f"[MONITOR] Visual session monitor initialized for {interface_type}")
        
    def _setup_screenshot_directory(self) -> str:
        """Create directory for storing screenshots"""
        screenshots_dir = os.path.expanduser("~/.dev-safety/screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir
        
    async def start_monitoring(self, check_interval: int = 30) -> None:
        """
        Start continuous visual monitoring
        
        IMPLEMENTATION STEPS (from handoff document):
        1. Initialize screenshot capture
        2. Start monitoring loop
        3. Take screenshots at intervals
        4. Analyze each screenshot
        5. Take action based on analysis
        
        Args:
            check_interval: Seconds between screenshot analysis
        """
        print(f"[MONITOR] Starting visual monitoring (interval: {check_interval}s)")
        
        if not pyautogui:
            print("[ERROR] Cannot start monitoring - pyautogui not available")
            return
            
        self.monitoring = True
        
        while self.monitoring:
            try:
                # Step 1 & 3: Capture screenshot
                screenshot_path = await self.capture_screenshot()
                
                if screenshot_path:
                    # Step 4: Analyze screenshot
                    analysis = await self.analyze_screenshot(screenshot_path)
                    
                    # Step 5: Take action based on analysis
                    await self.handle_analysis_result(analysis)
                    
                    # Update state tracking
                    self.last_analysis = analysis
                    self.state_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "analysis": analysis,
                        "screenshot_path": screenshot_path
                    })
                    
                    # Keep only last 50 states to prevent memory issues
                    if len(self.state_history) > 50:
                        self.state_history = self.state_history[-50:]
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"[ERROR] Monitoring loop error: {e}")
                await asyncio.sleep(check_interval)
                
        print("[MONITOR] Visual monitoring stopped")
        
    async def capture_screenshot(self) -> Optional[str]:
        """
        Capture screenshot of current screen
        
        Returns:
            Path to saved screenshot file, or None if capture failed
        """
        if not pyautogui:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.interface_type}_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            
            # Capture full screen
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            print(f"[SCREENSHOT] Saved: {filename}")
            return screenshot_path
            
        except Exception as e:
            print(f"[ERROR] Screenshot capture failed: {e}")
            return None
            
    async def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """
        Use AI to analyze screenshot and determine session state
        
        IMPLEMENTATION STEPS (from handoff document):
        1. Encode screenshot as base64
        2. Create analysis prompt for interface type
        3. Send to AI for analysis
        4. Parse response for session state
        5. Return structured analysis
        
        Args:
            screenshot_path: Path to screenshot file
            
        Returns:
            Dict with analysis results
        """
        try:
            # Step 1: Encode screenshot
            with open(screenshot_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Step 2: Create analysis prompt
            prompt = self._create_analysis_prompt()
            
            # Step 3: Send to AI for analysis (try OpenAI first, then Anthropic)
            if self.openai_client:
                analysis = await self._analyze_with_openai(image_data, prompt)
            elif self.anthropic_client:
                analysis = await self._analyze_with_anthropic(image_data, prompt)
            else:
                # Fallback: basic analysis based on screenshot metadata
                analysis = await self._analyze_fallback(screenshot_path)
            
            # Step 4 & 5: Parse and return structured analysis
            analysis["screenshot_path"] = screenshot_path
            analysis["analysis_timestamp"] = datetime.now().isoformat()
            analysis["interface_type"] = self.interface_type
            
            return analysis
            
        except Exception as e:
            print(f"[ERROR] Screenshot analysis failed: {e}")
            return {
                "status": "error", 
                "confidence": 0.0,
                "evidence": f"Analysis failed: {str(e)}",
                "recommended_action": "retry",
                "error": str(e)
            }
    
    def _create_analysis_prompt(self) -> str:
        """
        Create AI analysis prompt based on interface type
        
        This is from the original handoff document prompt design
        """
        base_prompt = f"""
        Analyze this screenshot of {self.interface_type} interface.
        
        Determine the current state by looking for these indicators:
        - Session active: "Claude is thinking", loading indicators, typing indicators
        - Session paused: "Continue" button visible, response truncated
        - Session ended: "Please start new conversation", "Start new chat", conversation limit reached
        - Rate limited: "You've reached your limit", rate limit messages, upgrade prompts
        - Error state: Error messages, "Something went wrong", connection issues
        - Ready for input: Active input box, "Send message" button, cursor in text area
        - Idle: Interface visible but no activity indicators
        
        Return JSON with:
        {{
            "status": "active|paused|ended|rate_limited|error|ready|idle",
            "confidence": 0.0-1.0,
            "evidence": "specific visual elements you see",
            "recommended_action": "wait|continue|new_session|retry|input_needed|none"
        }}
        """
        
        # Add interface-specific details
        if self.interface_type == "claude_desktop":
            base_prompt += """
            
            Claude Desktop specific indicators:
            - Look for the Claude desktop application window
            - "Continue" button appears when response is truncated
            - "New conversation" button in top-left for starting fresh
            - Dark/light theme variations
            - Side panel with conversation history
            """
        elif self.interface_type == "cursor":
            base_prompt += """
            
            Cursor IDE specific indicators:
            - Look for Cursor IDE interface with AI chat panel
            - Ctrl+L opens new chat
            - AI responses in chat sidebar
            - Code editor with AI suggestions
            """
        
        return base_prompt
    
    async def _analyze_with_openai(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Analyze screenshot using OpenAI GPT-4V"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                analysis = json.loads(content)
                analysis["analyzer"] = "openai_gpt4v"
                return analysis
            except json.JSONDecodeError:
                # If not JSON, create structured response
                return {
                    "status": "unknown",
                    "confidence": 0.5,
                    "evidence": content,
                    "recommended_action": "manual_review",
                    "analyzer": "openai_gpt4v"
                }
                
        except Exception as e:
            print(f"[ERROR] OpenAI analysis failed: {e}")
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"OpenAI analysis failed: {str(e)}",
                "recommended_action": "retry",
                "analyzer": "openai_gpt4v_error"
            }
    
    async def _analyze_with_anthropic(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Analyze screenshot using Anthropic Claude"""
        try:
            # Note: Anthropic's API for image analysis might be different
            # This is a placeholder implementation
            print("[INFO] Anthropic analysis not yet implemented")
            return {
                "status": "unknown",
                "confidence": 0.0,
                "evidence": "Anthropic analysis not implemented",
                "recommended_action": "manual_review",
                "analyzer": "anthropic_placeholder"
            }
            
        except Exception as e:
            print(f"[ERROR] Anthropic analysis failed: {e}")
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"Anthropic analysis failed: {str(e)}",
                "recommended_action": "retry",
                "analyzer": "anthropic_error"
            }
    
    async def _analyze_fallback(self, screenshot_path: str) -> Dict[str, Any]:
        """Fallback analysis when AI is not available"""
        try:
            # Basic analysis based on file size, timestamp, etc.
            file_size = os.path.getsize(screenshot_path)
            
            return {
                "status": "unknown",
                "confidence": 0.1,
                "evidence": f"Fallback analysis - screenshot captured ({file_size} bytes)",
                "recommended_action": "manual_review",
                "analyzer": "fallback"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"Fallback analysis failed: {str(e)}",
                "recommended_action": "retry",
                "analyzer": "fallback_error"
            }
    
    async def handle_analysis_result(self, analysis: Dict[str, Any]) -> None:
        """
        Take action based on screenshot analysis results
        
        Args:
            analysis: Analysis results from analyze_screenshot
        """
        status = analysis.get("status", "unknown")
        confidence = analysis.get("confidence", 0.0)
        recommended_action = analysis.get("recommended_action", "none")
        
        print(f"[ANALYSIS] Status: {status}, Confidence: {confidence:.2f}, Action: {recommended_action}")
        
        # Only take action if confidence is high enough
        if confidence < 0.7:
            print(f"[ACTION] Confidence too low ({confidence:.2f}) - no action taken")
            return
        
        action_taken = None
        
        try:
            if recommended_action == "continue" and status == "paused":
                action_taken = await self._click_continue_button()
                
            elif recommended_action == "new_session" and status == "ended":
                action_taken = await self._start_new_session()
                
            elif recommended_action == "retry" and status == "error":
                action_taken = await self._retry_last_action()
                
            elif recommended_action == "wait" and status == "active":
                action_taken = "waiting"
                print("[ACTION] Session active - waiting for completion")
                
            else:
                action_taken = "none"
                print(f"[ACTION] No action configured for {status}/{recommended_action}")
        
        except Exception as e:
            action_taken = f"error: {str(e)}"
            print(f"[ERROR] Action failed: {e}")
        
        # Log action
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "action_taken": action_taken
        })
        
    async def _click_continue_button(self) -> str:
        """Click the Continue button if available"""
        # This would be implemented by interface-specific handlers
        print("[ACTION] Would click Continue button (not implemented)")
        return "continue_clicked_simulated"
        
    async def _start_new_session(self) -> str:
        """Start a new session/conversation"""
        # This would be implemented by interface-specific handlers
        print("[ACTION] Would start new session (not implemented)")
        return "new_session_simulated"
        
    async def _retry_last_action(self) -> str:
        """Retry the last action"""
        print("[ACTION] Would retry last action (not implemented)")
        return "retry_simulated"
    
    def stop_monitoring(self) -> None:
        """Stop the visual monitoring loop"""
        print("[MONITOR] Stopping visual monitoring...")
        self.monitoring = False
        
    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis result"""
        return self.last_analysis
        
    def get_state_history(self, limit: int = 10) -> list:
        """Get recent state history"""
        return self.state_history[-limit:] if self.state_history else []
        
    def get_action_log(self, limit: int = 10) -> list:
        """Get recent action log"""
        return self.action_log[-limit:] if self.action_log else []
