import streamlit as st
from utils.auth import require_auth
from models.ticket import Ticket

def render_dashboard():
    require_auth()
    
    st.title("Support Dashboard")
    
    ticket_model = Ticket()
    tickets = ticket_model.get_all_tickets()
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_tickets = len(tickets)
    open_tickets = len([t for t in tickets if t['status'] == 'open'])
    high_priority = len([t for t in tickets if t['priority'] == 'high'])
    
    with col1:
        st.metric("Total Tickets", total_tickets)
    with col2:
        st.metric("Open Tickets", open_tickets)
    with col3:
        st.metric("High Priority", high_priority)
    with col4:
        response_rate = f"{((total_tickets - open_tickets) / total_tickets * 100) if total_tickets > 0 else 0:.1f}%"
        st.metric("Response Rate", response_rate)
    
    # Recent Tickets
    st.subheader("Recent Tickets")
    if tickets:
        for ticket in tickets[:5]:
            with st.expander(f"{ticket['title']} - {ticket['status'].upper()}"):
                st.write(f"Priority: {ticket['priority']}")
                st.write(f"Category: {ticket['category']}")
                st.write(f"Created by: {ticket['creator_email']}")
                if ticket['assignee_email']:
                    st.write(f"Assigned to: {ticket['assignee_email']}")
    else:
        st.info("No tickets found")
