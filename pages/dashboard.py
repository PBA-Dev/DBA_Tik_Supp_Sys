import streamlit as st
from utils.auth import require_auth
from models.ticket import Ticket
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from db.database import Database

def render_dashboard():
    require_auth()
    
    st.title("Support Dashboard")
    
    ticket_model = Ticket()
    db = Database()
    
    # Fetch tickets and create DataFrame
    tickets = ticket_model.get_all_tickets(
        user_id=st.session_state.user['id'],
        user_role=st.session_state.user['role']
    )
    df_tickets = pd.DataFrame(tickets)
    
    # Overview Statistics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_tickets = len(df_tickets)
    open_tickets = len(df_tickets[df_tickets['status'].str.lower() == 'open'])
    closed_tickets = len(df_tickets[df_tickets['status'].str.lower() == 'closed'])
    in_progress = len(df_tickets[df_tickets['status'].str.lower() == 'in progress'])
    
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
    
    # Ticket Trend Analysis
    st.markdown("---")
    st.subheader("Ticket Trends")
    
    # Convert created_at to datetime if it's not already
    df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'])
    
    # Daily ticket creation trend
    daily_tickets = df_tickets.groupby(df_tickets['created_at'].dt.date).size().reset_index()
    daily_tickets.columns = ['date', 'count']
    
    fig_trend = px.line(daily_tickets, x='date', y='count',
                        title='Daily Ticket Volume',
                        labels={'count': 'Number of Tickets', 'date': 'Date'})
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Category and Priority Distribution
    st.markdown("---")
    st.subheader("Ticket Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category distribution
        category_counts = df_tickets['category'].value_counts()
        fig_category = px.pie(values=category_counts.values, 
                            names=category_counts.index,
                            title='Tickets by Category')
        st.plotly_chart(fig_category, use_container_width=True)
        
    with col2:
        # Priority distribution
        priority_counts = df_tickets['priority'].value_counts()
        fig_priority = px.pie(values=priority_counts.values,
                            names=priority_counts.index,
                            title='Tickets by Priority')
        st.plotly_chart(fig_priority, use_container_width=True)
        
    # Status Timeline
    st.markdown("---")
    st.subheader("Status Timeline")
    
    status_daily = df_tickets.groupby([df_tickets['created_at'].dt.date, 'status']).size().unstack(fill_value=0)
    fig_timeline = px.area(status_daily, title='Ticket Status Over Time',
                          labels={'value': 'Number of Tickets', 'index': 'Date'})
    st.plotly_chart(fig_timeline, use_container_width=True)
        
    # Advanced Analytics (only for admin and agents)
    if st.session_state.user['role'] in ['admin', 'agent']:
        st.markdown("---")
        st.subheader("Advanced Analytics")
        
        # Priority Distribution
        priority_col1, priority_col2, priority_col3 = st.columns(3)
        
        low_priority = len(df_tickets[df_tickets['priority'].str.lower() == 'low'])
        medium_priority = len(df_tickets[df_tickets['priority'].str.lower() == 'medium'])
        high_priority = len(df_tickets[df_tickets['priority'].str.lower() == 'high'])
        
        with priority_col1:
            st.metric("Low Priority", low_priority)
        with priority_col2:
            st.metric("Medium Priority", medium_priority)
        with priority_col3:
            st.metric("High Priority", high_priority)
            
        # Agent Performance Metrics
        st.markdown("---")
        st.subheader("Agent Performance")
        
        if not df_tickets.empty and 'assignee_email' in df_tickets.columns:
            # Tickets per agent
            agent_tickets = df_tickets['assignee_email'].value_counts()
            fig_agent = px.bar(x=agent_tickets.index, y=agent_tickets.values,
                             title='Tickets Handled by Agent',
                             labels={'x': 'Agent', 'y': 'Number of Tickets'})
            st.plotly_chart(fig_agent, use_container_width=True)
            
            # Resolution rate per agent
            agent_resolution = df_tickets[df_tickets['status'].str.lower() == 'closed'].groupby('assignee_email').size()
            resolution_rate = (agent_resolution / agent_tickets * 100).round(2)
            
            st.subheader("Agent Resolution Rates")
            for agent, rate in resolution_rate.items():
                if agent:  # Skip None/unassigned
                    st.metric(f"{agent}", f"{rate}%")
        
        # Response Time Analysis
        st.markdown("---")
        st.subheader("Response Time Analysis")
        
        # Average resolution time by priority
        df_closed = df_tickets[df_tickets['status'].str.lower() == 'closed'].copy()
        if not df_closed.empty and 'created_at' in df_closed.columns and 'updated_at' in df_closed.columns:
            df_closed['resolution_time'] = (pd.to_datetime(df_closed['updated_at']) - 
                                         pd.to_datetime(df_closed['created_at'])).dt.total_seconds() / 3600  # in hours
            
            avg_resolution = df_closed.groupby('priority')['resolution_time'].mean().round(2)
            fig_resolution = px.bar(x=avg_resolution.index, y=avg_resolution.values,
                                  title='Average Resolution Time by Priority (Hours)',
                                  labels={'x': 'Priority', 'y': 'Hours'})
            st.plotly_chart(fig_resolution, use_container_width=True)
            
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
