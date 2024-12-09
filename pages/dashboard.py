import streamlit as st
from utils.auth import require_auth
from models.ticket import Ticket

def render_dashboard():
    require_auth()
    
    st.title("Support Dashboard")
    
    ticket_model = Ticket()
    tickets = ticket_model.get_all_tickets(
        user_id=st.session_state.user['id'],
        user_role=st.session_state.user['role']
    )
    
    # Statistics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_tickets = len(tickets)
    open_tickets = len([t for t in tickets if t['status'].lower() == 'open'])
    closed_tickets = len([t for t in tickets if t['status'].lower() == 'closed'])
    in_progress = len([t for t in tickets if t['status'].lower() == 'in progress'])
    
    with col1:
        st.metric("Total Tickets", total_tickets)
    with col2:
        st.metric("Open Tickets", open_tickets)
    with col3:
        st.metric("Closed Tickets", closed_tickets)
    with col4:
        st.metric("In Progress", in_progress)
    with col5:
        response_rate = f"{(closed_tickets / total_tickets * 100) if total_tickets > 0 else 0:.1f}%"
        st.metric("Response Rate", response_rate)
        
    # Priority Statistics (only for admin and agents)
    if st.session_state.user['role'] in ['admin', 'agent']:
        st.markdown("---")
        priority_col1, priority_col2, priority_col3 = st.columns(3)
        
        low_priority = len([t for t in tickets if t['priority'].lower() == 'low'])
        medium_priority = len([t for t in tickets if t['priority'].lower() == 'medium'])
        high_priority = len([t for t in tickets if t['priority'].lower() == 'high'])
        
        with priority_col1:
            st.metric("Low Priority", low_priority)
        with priority_col2:
            st.metric("Medium Priority", medium_priority)
        with priority_col3:
            st.metric("High Priority", high_priority)
            
    # Custom CSS for high priority tickets
    if st.session_state.user['role'] in ['admin', 'agent']:
        st.markdown("""
        <style>
        .high-priority {
            border: 2px solid red !important;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Recent Tickets
    st.subheader("Recent Tickets")
    if tickets:
        for ticket in tickets[:5]:
            # Add high-priority class if applicable
            is_high_priority = ticket['priority'].lower() == 'high' and st.session_state.user['role'] in ['admin', 'agent']
            
            if is_high_priority:
                st.markdown('<div class="high-priority">', unsafe_allow_html=True)
                
            with st.expander(f"{ticket['title']} - {ticket['status'].upper()}"):
                st.write(f"Priority: {ticket['priority']}")
                st.write(f"Category: {ticket['category']}")
                st.write(f"Created by: {ticket['creator_email']}")
                if ticket['assignee_email']:
                    st.write(f"Assigned to: {ticket['assignee_email']}")
                    
            if is_high_priority:
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No tickets found")
