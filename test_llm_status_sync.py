#!/usr/bin/env python3
"""Test script to verify LLM status synchronization."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

async def test_llm_status():
    """Test LLM status updates."""
    print("🧪 Testing LLM Status Synchronization")
    print("=" * 50)
    
    # Test the status broadcasting function
    from backend.services.ollama.ollama_streaming import _update_llm_status, llm_status
    
    print("📡 Testing status updates...")
    
    # Test different status values
    statuses = ["loading...", "connected...", "thinking...", "", "error"]
    
    for status in statuses:
        print(f"  Setting status to: '{status}'")
        await _update_llm_status(status)
        
        # Import after the update to get current value
        from backend.services.ollama.ollama_streaming import llm_status as current_status
        print(f"  Current status: '{current_status}'")
        
        await asyncio.sleep(0.1)  # Small delay to simulate real usage
    
    print("\n✅ Status updates completed!")
    print("📋 Note: In a real scenario, these would be broadcast to all WebSocket clients")

if __name__ == "__main__":
    asyncio.run(test_llm_status())
