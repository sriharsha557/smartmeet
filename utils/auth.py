# utils/auth.py
import os
import requests
from typing import Dict, Optional
import streamlit as st
from datetime import datetime, timedelta

class MicrosoftAuthenticator:
    def __init__(self):
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', 'common')
        self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:8501/auth/callback')
        
        # Microsoft Graph endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
        self.auth_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
        
        # Required scopes for calendar access
        self.scopes = [
            'https://graph.microsoft.com/Calendars.ReadWrite',
            'https://graph.microsoft.com/User.Read',
            'https://graph.microsoft.com/Mail.Send'
        ]
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate Microsoft OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_mode': 'query',
            'state': state or 'default_state'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_endpoint}?{query_string}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Microsoft client credentials not configured")
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code',
            'scope': ' '.join(self.scopes)
        }
        
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Microsoft client credentials not configured")
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'scope': ' '.join(self.scopes)
        }
        
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Microsoft Graph"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def is_token_expired(self, token_data: Dict) -> bool:
        """Check if access token is expired"""
        if 'expires_at' not in token_data:
            return True
        
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        return datetime.now() >= expires_at
    
    def store_tokens(self, token_data: Dict) -> None:
        """Store tokens in session state with expiration time"""
        # Calculate expiration time
        expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        st.session_state.microsoft_tokens = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': expires_at.isoformat(),
            'token_type': token_data.get('token_type', 'Bearer')
        }
    
    def get_valid_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        if 'microsoft_tokens' not in st.session_state:
            return None
        
        token_data = st.session_state.microsoft_tokens
        
        # Check if token is expired
        if self.is_token_expired(token_data):
            if token_data.get('refresh_token'):
                try:
                    # Refresh the token
                    new_tokens = self.refresh_access_token(token_data['refresh_token'])
                    self.store_tokens(new_tokens)
                    return new_tokens['access_token']
                except Exception as e:
                    st.error(f"Failed to refresh token: {e}")
                    return None
            else:
                return None
        
        return token_data['access_token']

def authenticate_microsoft() -> bool:
    """Main authentication function for Streamlit app"""
    authenticator = MicrosoftAuthenticator()
    
    # Check if already authenticated
    if 'microsoft_tokens' in st.session_state:
        access_token = authenticator.get_valid_access_token()
        if access_token:
            return True
    
    # Handle OAuth callback
    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        try:
            authorization_code = query_params['code'][0]
            tokens = authenticator.exchange_code_for_tokens(authorization_code)
            authenticator.store_tokens(tokens)
            
            # Get user info
            user_info = authenticator.get_user_info(tokens['access_token'])
            st.session_state.user_info = user_info
            
            st.success("Successfully authenticated with Microsoft!")
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            return False
    
    return False

def get_auth_button():
    """Display authentication button"""
    authenticator = MicrosoftAuthenticator()
    
    if not authenticator.client_id:
        st.warning("⚠️ Microsoft authentication not configured. Set MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, and MICROSOFT_TENANT_ID environment variables.")
        return False
    
    auth_url = authenticator.get_auth_url()
    st.markdown(f'<a href="{auth_url}" target="_self">🔐 Connect to Microsoft 365</a>', unsafe_allow_html=True)
    
    return False

def logout():
    """Clear authentication tokens"""
    if 'microsoft_tokens' in st.session_state:
        del st.session_state.microsoft_tokens
    if 'user_info' in st.session_state:
        del st.session_state.user_info
    st.experimental_rerun()