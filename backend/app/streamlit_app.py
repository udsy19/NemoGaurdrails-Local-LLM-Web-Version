import streamlit as st
import requests
import json
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Configuration - use same port as backend
BACKEND_URL = "http://localhost:8000"

def check_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/chat/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_detector_status():
    """Get status of all detectors"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/detectors/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Convert list format to dict format for easier processing
            if 'detectors' in data:
                detector_dict = {}
                for detector in data['detectors']:
                    detector_dict[detector['name']] = detector
                return detector_dict
            return data
        return {}
    except:
        return {}

def send_chat_message(message, detectors=None):
    """Send message to chat API"""
    try:
        payload = {"message": message}
        # Always send detector config, even if empty list
        # Empty list means no detectors should be active
        detector_config = {}
        if detectors is not None:  # Check for None, not just truthiness
            for detector in detectors:
                detector_config[detector] = {"enabled": True}
        payload["detector_config"] = detector_config
        
        response = requests.post(
            f"{BACKEND_URL}/api/chat/message",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    st.set_page_config(
        page_title="AI Safety System",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🛡️ AI Safety System")
    st.markdown("**NeMo Guardrails Local LLM Protection - Single Port Edition**")
    
    # Check backend status
    backend_status = check_backend_status()
    
    # Status indicator
    col1, col2 = st.columns([3, 1])
    with col2:
        if backend_status:
            st.success("🟢 Backend Online")
        else:
            st.error("🔴 Backend Offline")
            st.warning("Backend not responding. Check if it's running on port 8000.")
            return
    
    # Sidebar for detector settings
    with st.sidebar:
        st.header("🔧 Detector Settings")
        
        # Get detector status
        detectors = get_detector_status()
        
        if detectors:
            st.subheader("Available Detectors")
            enabled_detectors = []
            
            # Debug: Show raw detector data
            if st.checkbox("🔍 Show Debug Info"):
                st.write("Raw detector data:", detectors)
            
            # Handle different response formats
            if isinstance(detectors, dict):
                for detector_name, detector_info in detectors.items():
                    # Handle both simple and complex detector info formats
                    if isinstance(detector_info, dict):
                        loaded = detector_info.get('loaded', detector_info.get('status') == 'loaded')
                        active = detector_info.get('active', True)
                        enabled_default = loaded and active
                        description = detector_info.get('description', 'No description available')
                    else:
                        loaded = True  # Assume loaded if simple format
                        active = True
                        enabled_default = True
                        description = 'No description available'
                    
                    enabled = st.checkbox(
                        f"{detector_name.title()} Detection",
                        value=enabled_default,
                        help=f"Status: {'✅ Loaded & Active' if loaded and active else '❌ Not Ready'}\n{description}"
                    )
                    if enabled:
                        enabled_detectors.append(detector_name)
            
            st.session_state['enabled_detectors'] = enabled_detectors
        else:
            st.warning("Could not load detector information")
            st.info("Trying to connect to backend...")
        
        # System metrics
        st.subheader("📊 System Metrics")
        if 'chat_history' in st.session_state:
            total_messages = len(st.session_state.chat_history)
            blocked_messages = sum(1 for msg in st.session_state.chat_history if msg.get('blocked'))
            st.metric("Total Messages", total_messages)
            st.metric("Blocked Messages", blocked_messages)
            if total_messages > 0:
                block_rate = (blocked_messages / total_messages) * 100
                st.metric("Block Rate", f"{block_rate:.1f}%")
    
    # Main chat interface
    st.header("💬 Chat Interface")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat input
    with st.container():
        message = st.text_area(
            "Enter your message:",
            height=100,
            placeholder="Type your message here..."
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            send_button = st.button("Send Message", type="primary")
        with col2:
            clear_button = st.button("Clear History")
    
    # Handle clear button
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    # Handle send button
    if send_button and message.strip():
        with st.spinner("Processing message..."):
            # Get enabled detectors
            enabled_detectors = st.session_state.get('enabled_detectors', [])
            
            # Send message
            result = send_chat_message(message, enabled_detectors)
            
            if result:
                # Add to chat history
                chat_entry = {
                    "timestamp": datetime.now(),
                    "user_message": message,
                    "result": result,
                    "blocked": result.get("blocked", False)
                }
                st.session_state.chat_history.append(chat_entry)
        
        # Clear the input
        st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("📝 Chat History")
        
        # Add custom CSS for better scrolling behavior
        st.markdown("""
        <style>
        .main .block-container {
            max-width: 100%;
            padding-top: 1rem;
        }
        .stExpander > div:first-child {
            background-color: #f0f2f6;
        }
        /* Auto scroll to bottom */
        .element-container:last-child {
            margin-bottom: 20px;
        }
        </style>
        <script>
        // Auto scroll to bottom when new messages are added
        setTimeout(function() {
            window.scrollTo(0, document.body.scrollHeight);
        }, 100);
        </script>
        """, unsafe_allow_html=True)
        
        # Chat controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            show_recent_only = st.checkbox("Show recent messages only", value=True)
        with col2:
            if len(st.session_state.chat_history) > 0:
                st.caption(f"Total: {len(st.session_state.chat_history)} messages")
        
        # Always show messages in chronological order (oldest first, newest last)
        messages_to_display = st.session_state.chat_history
        
        # If showing recent only, limit to last 5 messages
        if show_recent_only and len(st.session_state.chat_history) > 5:
            messages_to_display = st.session_state.chat_history[-5:]
            st.info(f"Showing last 5 messages. Uncheck 'Show recent messages only' to see all {len(st.session_state.chat_history)} messages.")
        
        # Display messages in chronological order (oldest to newest)
        for i, entry in enumerate(messages_to_display):
            # Calculate the actual message number
            if show_recent_only and len(st.session_state.chat_history) > 5:
                message_num = len(st.session_state.chat_history) - 5 + i + 1
            else:
                message_num = i + 1
            
            # Create a unique key for each message
            message_key = f"msg_{message_num}_{entry['timestamp'].strftime('%H%M%S')}"
            
            # Expand the most recent message, collapse others
            is_most_recent = (i == len(messages_to_display) - 1)
            
            with st.expander(f"Message {message_num} - {entry['timestamp'].strftime('%H:%M:%S')}", expanded=is_most_recent, key=message_key):
                
                # User message
                st.markdown("**👤 User:**")
                st.text(entry['user_message'])
                
                result = entry['result']
                
                # Check if blocked
                if result.get('blocked'):
                    st.error("🚫 **Message Blocked by AI Safety System**")
                    
                    # Show blocking reasons
                    blocking_reasons = result.get('blocking_reasons', [])
                    if blocking_reasons:
                        st.markdown("**Blocking Reasons:**")
                        for reason in blocking_reasons:
                            st.error(f"❌ {reason}")
                    
                    # Show detection results
                    input_analysis = result.get('input_analysis', {})
                    output_analysis = result.get('output_analysis', {})
                    
                    if input_analysis or output_analysis:
                        st.markdown("**Detection Results:**")
                        
                        if input_analysis:
                            st.markdown("*Input Analysis:*")
                            for detector, detection_result in input_analysis.items():
                                if isinstance(detection_result, dict):
                                    blocked = detection_result.get('blocked', False)
                                    confidence = detection_result.get('confidence', 0)
                                    reason = detection_result.get('reason', 'No reason provided')
                                    
                                    if blocked:
                                        st.error(f"❌ **{detector.title()}**: {reason} (Confidence: {confidence:.2f})")
                                    else:
                                        st.success(f"✅ **{detector.title()}**: Safe (Confidence: {confidence:.2f})")
                        
                        if output_analysis:
                            st.markdown("*Output Analysis:*")
                            for detector, detection_result in output_analysis.items():
                                if isinstance(detection_result, dict):
                                    blocked = detection_result.get('blocked', False)
                                    confidence = detection_result.get('confidence', 0)
                                    reason = detection_result.get('reason', 'No reason provided')
                                    
                                    if blocked:
                                        st.error(f"❌ **{detector.title()}**: {reason} (Confidence: {confidence:.2f})")
                                    else:
                                        st.success(f"✅ **{detector.title()}**: Safe (Confidence: {confidence:.2f})")
                else:
                    # AI response
                    ai_response = result.get('response', 'No response')
                    st.markdown("**🤖 AI Assistant:**")
                    st.markdown(ai_response)
                    
                    # Show detection results for non-blocked messages
                    input_analysis = result.get('input_analysis', {})
                    output_analysis = result.get('output_analysis', {})
                    
                    if input_analysis or output_analysis:
                        with st.expander("🔍 Detection Details"):
                            if input_analysis:
                                st.markdown("*Input Analysis:*")
                                for detector, detection_result in input_analysis.items():
                                    if isinstance(detection_result, dict):
                                        confidence = detection_result.get('confidence', 0)
                                        st.success(f"✅ **{detector.title()}**: Safe (Confidence: {confidence:.2f})")
                            
                            if output_analysis:
                                st.markdown("*Output Analysis:*")
                                for detector, detection_result in output_analysis.items():
                                    if isinstance(detection_result, dict):
                                        confidence = detection_result.get('confidence', 0)
                                        st.success(f"✅ **{detector.title()}**: Safe (Confidence: {confidence:.2f})")
                
                st.divider()
        
        # Auto-scroll anchor point
        if st.session_state.chat_history:
            st.markdown("""
            <div id="chat-bottom"></div>
            <script>
            // Force scroll to bottom after page load
            setTimeout(function() {
                document.getElementById('chat-bottom').scrollIntoView({behavior: 'smooth'});
            }, 200);
            </script>
            """, unsafe_allow_html=True)
    
    # Analytics Dashboard
    if st.session_state.chat_history:
        st.header("📈 Analytics Dashboard")
        
        # Create metrics DataFrame
        df_data = []
        for entry in st.session_state.chat_history:
            result = entry['result']
            input_analysis = result.get('input_analysis', {})
            output_analysis = result.get('output_analysis', {})
            
            # Combine input and output analysis
            all_detections = {}
            if input_analysis and isinstance(input_analysis, dict):
                all_detections.update(input_analysis)
            if output_analysis and isinstance(output_analysis, dict):
                all_detections.update(output_analysis)
            
            for detector, detection_result in all_detections.items():
                if isinstance(detection_result, dict):
                    df_data.append({
                        'timestamp': entry['timestamp'],
                        'detector': detector,
                        'blocked': detection_result.get('blocked', False),
                        'confidence': detection_result.get('confidence', 0)
                    })
        
        if df_data:
            df = pd.DataFrame(df_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Detection counts by detector
                detection_counts = df.groupby(['detector', 'blocked']).size().reset_index(name='count')
                fig_bar = px.bar(
                    detection_counts, 
                    x='detector', 
                    y='count', 
                    color='blocked',
                    title="Detection Results by Detector",
                    color_discrete_map={True: 'red', False: 'green'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Confidence distribution
                fig_hist = px.histogram(
                    df, 
                    x='confidence', 
                    color='blocked',
                    title="Confidence Score Distribution",
                    nbins=20,
                    color_discrete_map={True: 'red', False: 'green'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            # Timeline
            if len(df) > 1:
                timeline_data = df.groupby(['timestamp', 'blocked']).size().reset_index(name='count')
                fig_timeline = px.line(
                    timeline_data, 
                    x='timestamp', 
                    y='count', 
                    color='blocked',
                    title="Detection Timeline",
                    color_discrete_map={True: 'red', False: 'green'}
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

if __name__ == "__main__":
    main()