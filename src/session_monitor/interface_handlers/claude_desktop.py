"""
Claude Desktop Interface Handler

Interface-specific automation for Claude Desktop application.
Implements the handlers outlined in the original handoff document Phase 2.2.

This module handles:
- Claude Desktop window detection
- UI element identification and interaction
- Session state detection specific to Claude Desktop
- Automated actions (Continue, New Conversation, etc.)
"""

import time
from typing import Dict, Any, Optional, Tuple

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None
    print("Warning: pyautogui not installed - Claude Desktop automation disabled")

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None
    print("Warning: opencv-python not installed - advanced image detection disabled")


class ClaudeDesktopHandler:
    """
    Claude Desktop specific automation handler
    
    Implements the interface handler pattern from the original handoff document:
    - Window detection and focus
    - UI element location and interaction
    - Session state detection
    - Automated response to session changes
    """
    
    def __init__(self):
        """Initialize Claude Desktop handler"""
        self.window_title = "Claude"
        self.last_window_position = None
        self.ui_elements = {
            "continue_button": None,
            "new_conversation_button": None,
            "input_area": None,
            "send_button": None
        }
        
        print("[CLAUDE] Claude Desktop handler initialized")
        
    async def detect_session_state(self) -> Dict[str, Any]:
        """
        Detect current session state in Claude Desktop
        
        IMPLEMENTATION STEPS (from handoff document):
        1. Find Claude Desktop window
        2. Take screenshot of Claude window
        3. Look for specific UI elements
        4. Return session state
        
        Returns:
            Dict with session state information
        """
        try:
            # Step 1: Find Claude Desktop window
            window_info = await self._find_claude_window()
            
            if not window_info["found"]:
                return {
                    "status": "window_not_found",
                    "confidence": 1.0,
                    "evidence": "Claude Desktop window not detected",
                    "recommended_action": "launch_claude",
                    "window_info": window_info
                }
            
            # Step 2: Take screenshot of Claude window
            window_screenshot = await self._capture_window_screenshot(window_info)
            
            if not window_screenshot:
                return {
                    "status": "screenshot_failed",
                    "confidence": 0.8,
                    "evidence": "Could not capture Claude window",
                    "recommended_action": "retry",
                    "window_info": window_info
                }
            
            # Step 3: Look for specific UI elements
            ui_analysis = await self._analyze_claude_ui(window_screenshot)
            
            # Step 4: Return session state based on UI analysis
            return {
                "status": ui_analysis["status"],
                "confidence": ui_analysis["confidence"],
                "evidence": ui_analysis["evidence"],
                "recommended_action": ui_analysis["recommended_action"],
                "window_info": window_info,
                "ui_elements": ui_analysis["ui_elements"],
                "screenshot_path": window_screenshot
            }
            
        except Exception as e:
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"Detection failed: {str(e)}",
                "recommended_action": "retry",
                "error": str(e)
            }
    
    async def _find_claude_window(self) -> Dict[str, Any]:
        """
        Find Claude Desktop window
        
        Returns:
            Dict with window information
        """
        if not pyautogui:
            return {"found": False, "reason": "pyautogui not available"}
        
        try:
            # Try to find window by title
            windows = pyautogui.getWindowsWithTitle(self.window_title)
            
            if windows:
                window = windows[0]  # Get first Claude window
                
                # Check if window is minimized or hidden
                if window.isMinimized:
                    window.restore()
                    time.sleep(0.5)  # Wait for window to restore
                
                # Bring window to front
                window.activate()
                time.sleep(0.2)
                
                window_info = {
                    "found": True,
                    "title": window.title,
                    "left": window.left,
                    "top": window.top, 
                    "width": window.width,
                    "height": window.height,
                    "is_maximized": window.isMaximized,
                    "is_active": window.isActive
                }
                
                self.last_window_position = window_info
                return window_info
            else:
                return {
                    "found": False,
                    "reason": "No Claude Desktop window found",
                    "searched_title": self.window_title
                }
                
        except Exception as e:
            return {
                "found": False,
                "reason": f"Window detection failed: {str(e)}",
                "error": str(e)
            }
    
    async def _capture_window_screenshot(self, window_info: Dict[str, Any]) -> Optional[str]:
        """
        Capture screenshot of Claude window specifically
        
        Args:
            window_info: Window information from _find_claude_window
            
        Returns:
            Path to screenshot file or None if failed
        """
        if not pyautogui or not window_info["found"]:
            return None
            
        try:
            # Define screenshot region based on window position
            left = window_info["left"]
            top = window_info["top"]
            width = window_info["width"]
            height = window_info["height"]
            
            # Capture specific window region
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            
            # Save screenshot
            import os
            from datetime import datetime
            
            screenshots_dir = os.path.expanduser("~/.dev-safety/screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_window_{timestamp}.png"
            screenshot_path = os.path.join(screenshots_dir, filename)
            
            screenshot.save(screenshot_path)
            
            print(f"[CLAUDE] Window screenshot saved: {filename}")
            return screenshot_path
            
        except Exception as e:
            print(f"[ERROR] Claude window screenshot failed: {e}")
            return None
    
    async def _analyze_claude_ui(self, screenshot_path: str) -> Dict[str, Any]:
        """
        Analyze Claude Desktop UI elements to determine session state
        
        Args:
            screenshot_path: Path to Claude window screenshot
            
        Returns:
            Dict with UI analysis results
        """
        try:
            ui_elements_found = {}
            evidence_list = []
            
            # Basic file-based analysis (fallback when CV2 not available)
            if not cv2:
                return await self._analyze_ui_fallback(screenshot_path)
            
            # Load screenshot for analysis
            image = cv2.imread(screenshot_path)
            if image is None:
                return {
                    "status": "error",
                    "confidence": 0.0,
                    "evidence": "Could not load screenshot for analysis",
                    "recommended_action": "retry",
                    "ui_elements": {}
                }
            
            # Look for specific UI patterns
            
            # 1. Continue button detection
            continue_found = await self._detect_continue_button(image)
            if continue_found:
                ui_elements_found["continue_button"] = continue_found
                evidence_list.append("Continue button detected")
            
            # 2. New conversation button detection
            new_conv_found = await self._detect_new_conversation_button(image)
            if new_conv_found:
                ui_elements_found["new_conversation_button"] = new_conv_found
                evidence_list.append("New conversation button detected")
            
            # 3. Input area detection
            input_found = await self._detect_input_area(image)
            if input_found:
                ui_elements_found["input_area"] = input_found
                evidence_list.append("Input area detected")
            
            # 4. Thinking indicator detection
            thinking_found = await self._detect_thinking_indicator(image)
            if thinking_found:
                ui_elements_found["thinking_indicator"] = thinking_found
                evidence_list.append("Thinking indicator detected")
            
            # Determine overall session state based on found elements
            status, confidence, action = self._determine_session_status(ui_elements_found)
            
            return {
                "status": status,
                "confidence": confidence,
                "evidence": "; ".join(evidence_list) if evidence_list else "No specific elements detected",
                "recommended_action": action,
                "ui_elements": ui_elements_found
            }
            
        except Exception as e:
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"UI analysis failed: {str(e)}",
                "recommended_action": "retry",
                "ui_elements": {},
                "error": str(e)
            }
    
    async def _analyze_ui_fallback(self, screenshot_path: str) -> Dict[str, Any]:
        """Fallback UI analysis when OpenCV is not available"""
        try:
            # Basic file-based analysis
            import os
            file_size = os.path.getsize(screenshot_path)
            
            return {
                "status": "unknown",
                "confidence": 0.3,
                "evidence": f"Fallback analysis - screenshot captured ({file_size} bytes)",
                "recommended_action": "manual_review",
                "ui_elements": {}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"Fallback analysis failed: {str(e)}",
                "recommended_action": "retry",
                "ui_elements": {}
            }
    
    async def _detect_continue_button(self, image) -> Optional[Dict[str, Any]]:
        """Detect Continue button in Claude interface"""
        # This would implement template matching or text recognition
        # For now, return placeholder
        return None
    
    async def _detect_new_conversation_button(self, image) -> Optional[Dict[str, Any]]:
        """Detect New Conversation button in Claude interface"""
        # This would implement template matching or text recognition
        # For now, return placeholder
        return None
    
    async def _detect_input_area(self, image) -> Optional[Dict[str, Any]]:
        """Detect input text area in Claude interface"""
        # This would implement template matching or text recognition
        # For now, return placeholder
        return None
    
    async def _detect_thinking_indicator(self, image) -> Optional[Dict[str, Any]]:
        """Detect 'Claude is thinking' indicator"""
        # This would implement template matching or text recognition
        # For now, return placeholder
        return None
    
    def _determine_session_status(self, ui_elements: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Determine session status based on detected UI elements
        
        Returns:
            Tuple of (status, confidence, recommended_action)
        """
        if ui_elements.get("thinking_indicator"):
            return "active", 0.9, "wait"
        elif ui_elements.get("continue_button"):
            return "paused", 0.9, "continue"
        elif ui_elements.get("input_area") and not ui_elements.get("thinking_indicator"):
            return "ready", 0.8, "input_needed"
        else:
            return "unknown", 0.3, "manual_review"
    
    async def click_continue(self) -> bool:
        """
        Click the Continue button
        
        IMPLEMENTATION STEPS (from handoff document):
        1. Find "Continue" button coordinates
        2. Click button using pyautogui
        3. Wait for response
        4. Return success status
        """
        if not pyautogui:
            print("[ERROR] Cannot click Continue - pyautogui not available")
            return False
        
        try:
            # Step 1: Find Continue button
            continue_location = await self._locate_continue_button()
            
            if not continue_location:
                print("[ERROR] Continue button not found")
                return False
            
            # Step 2: Click button
            x, y = continue_location["center"]
            pyautogui.click(x, y)
            print(f"[CLAUDE] Clicked Continue button at ({x}, {y})")
            
            # Step 3: Wait for response
            time.sleep(1.0)
            
            # Step 4: Return success
            return True
            
        except Exception as e:
            print(f"[ERROR] Click Continue failed: {e}")
            return False
    
    async def start_new_conversation(self) -> bool:
        """
        Start a new conversation
        
        IMPLEMENTATION STEPS (from handoff document):
        1. Find "New conversation" button
        2. Click to start new chat
        3. Wait for interface to be ready
        4. Return success status
        """
        if not pyautogui:
            print("[ERROR] Cannot start new conversation - pyautogui not available")
            return False
        
        try:
            # Step 1: Find New Conversation button
            new_conv_location = await self._locate_new_conversation_button()
            
            if not new_conv_location:
                print("[ERROR] New conversation button not found")
                return False
            
            # Step 2: Click button
            x, y = new_conv_location["center"]
            pyautogui.click(x, y)
            print(f"[CLAUDE] Clicked New Conversation button at ({x}, {y})")
            
            # Step 3: Wait for interface to be ready
            time.sleep(2.0)
            
            # Step 4: Return success
            return True
            
        except Exception as e:
            print(f"[ERROR] Start new conversation failed: {e}")
            return False
    
    async def _locate_continue_button(self) -> Optional[Dict[str, Any]]:
        """Locate Continue button on screen"""
        # This would implement button detection
        # For now, return placeholder
        print("[INFO] Continue button location not implemented - returning mock position")
        return {"center": (400, 500), "confidence": 0.5}
    
    async def _locate_new_conversation_button(self) -> Optional[Dict[str, Any]]:
        """Locate New Conversation button on screen"""
        # This would implement button detection
        # For now, return placeholder
        print("[INFO] New conversation button location not implemented - returning mock position")
        return {"center": (100, 100), "confidence": 0.5}
    
    async def send_message(self, message: str) -> bool:
        """
        Send a message to Claude Desktop
        
        Args:
            message: Message text to send
            
        Returns:
            True if message sent successfully
        """
        if not pyautogui:
            print("[ERROR] Cannot send message - pyautogui not available")
            return False
        
        try:
            # Find and click input area
            input_location = await self._locate_input_area()
            
            if input_location:
                x, y = input_location["center"]
                pyautogui.click(x, y)
                time.sleep(0.2)
                
                # Type message
                pyautogui.typewrite(message)
                time.sleep(0.1)
                
                # Send message (Enter key)
                pyautogui.press('enter')
                
                print(f"[CLAUDE] Sent message: {message[:50]}...")
                return True
            else:
                print("[ERROR] Input area not found")
                return False
                
        except Exception as e:
            print(f"[ERROR] Send message failed: {e}")
            return False
    
    async def _locate_input_area(self) -> Optional[Dict[str, Any]]:
        """Locate input text area"""
        # This would implement input area detection
        # For now, return placeholder
        print("[INFO] Input area location not implemented - returning mock position")
        return {"center": (400, 600), "confidence": 0.5}
    
    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """Get current window information"""
        return self.last_window_position
