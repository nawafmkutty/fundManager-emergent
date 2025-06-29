import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);

  // Auth forms
  const [isLogin, setIsLogin] = useState(true);
  const [authForm, setAuthForm] = useState({
    email: '',
    password: '',
    full_name: '',
    country: '',
    phone: ''
  });

  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [applications, setApplications] = useState([]);
  const [repayments, setRepayments] = useState([]);
  const [adminData, setAdminData] = useState({
    users: [],
    allApplications: [],
    allDeposits: []
  });

  // Form states
  const [depositForm, setDepositForm] = useState({ amount: '', description: '' });
  const [applicationForm, setApplicationForm] = useState({
    amount: '',
    purpose: '',
    requested_duration_months: '',
    description: ''
  });

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  const api = async (endpoint, options = {}) => {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      ...options
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    const response = await fetch(`${API_URL}${endpoint}`, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Network error' }));
      throw new Error(error.detail || 'Something went wrong');
    }
    
    return response.json();
  };

  const fetchUserProfile = async () => {
    try {
      const userData = await api('/api/auth/me');
      setUser(userData);
      fetchDashboard();
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    }
  };

  const fetchDashboard = async () => {
    try {
      const dashboardData = await api('/api/dashboard');
      setDashboard(dashboardData);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    }
  };

  const fetchDeposits = async () => {
    try {
      const depositsData = await api('/api/deposits');
      setDeposits(depositsData);
    } catch (error) {
      console.error('Failed to fetch deposits:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const applicationsData = await api('/api/finance-applications');
      setApplications(applicationsData);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
    }
  };

  const fetchRepayments = async () => {
    try {
      const repaymentsData = await api('/api/repayments');
      setRepayments(repaymentsData);
    } catch (error) {
      console.error('Failed to fetch repayments:', error);
    }
  };

  const fetchAdminData = async () => {
    try {
      if (isAdmin()) {
        const [usersData, applicationsData, depositsData] = await Promise.all([
          api('/api/admin/users').catch(() => []),
          api('/api/admin/applications').catch(() => []),
          api('/api/admin/deposits').catch(() => [])
        ]);
        
        setAdminData({
          users: usersData,
          allApplications: applicationsData,
          allDeposits: depositsData
        });
      }
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin 
        ? { email: authForm.email, password: authForm.password }
        : authForm;

      const data = await api(endpoint, { method: 'POST', body });
      
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      fetchDashboard();
      
      setAuthForm({ email: '', password: '', full_name: '', country: '', phone: '' });
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    setActiveTab('dashboard');
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api('/api/deposits', { 
        method: 'POST', 
        body: { 
          amount: parseFloat(depositForm.amount),
          description: depositForm.description 
        }
      });
      
      setDepositForm({ amount: '', description: '' });
      fetchDashboard();
      fetchDeposits();
      alert('Deposit recorded successfully!');
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const handleApplication = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api('/api/finance-applications', {
        method: 'POST',
        body: {
          amount: parseFloat(applicationForm.amount),
          purpose: applicationForm.purpose,
          requested_duration_months: parseInt(applicationForm.requested_duration_months),
          description: applicationForm.description
        }
      });

      setApplicationForm({ amount: '', purpose: '', requested_duration_months: '', description: '' });
      fetchDashboard();
      fetchApplications();
      alert('Finance application submitted successfully!');
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const updateUserRole = async (userId, newRole) => {
    try {
      await api('/api/admin/users/role', {
        method: 'PUT',
        body: { user_id: userId, new_role: newRole }
      });
      
      fetchAdminData();
      alert('User role updated successfully!');
    } catch (error) {
      alert(error.message);
    }
  };

  const updateApplicationStatus = async (applicationId, status, notes = '') => {
    try {
      await api(`/api/admin/applications/${applicationId}/status`, {
        method: 'PUT',
        body: { status, review_notes: notes }
      });
      
      fetchAdminData();
      fetchApplications();
      alert('Application status updated successfully!');
    } catch (error) {
      alert(error.message);
    }
  };

  const isAdmin = () => {
    return user && ['country_coordinator', 'fund_admin', 'general_admin'].includes(user.role);
  };

  const isGeneralAdmin = () => {
    return user && user.role === 'general_admin';
  };

  const isFundAdmin = () => {
    return user && ['fund_admin', 'general_admin'].includes(user.role);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      under_review: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      disbursed: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      paid: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getRoleBadge = (role) => {
    const colors = {
      member: 'bg-gray-100 text-gray-800',
      country_coordinator: 'bg-blue-100 text-blue-800',
      fund_admin: 'bg-purple-100 text-purple-800',
      general_admin: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[role] || 'bg-gray-100 text-gray-800'}`}>
        {role.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Fund Manager</h1>
            <p className="text-gray-600">Your personal finance companion</p>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Admin Login:</p>
              <p className="text-xs text-blue-600">Email: admin@fundmanager.com</p>
              <p className="text-xs text-blue-600">Password: FundAdmin2024!</p>
            </div>
          </div>

          <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                !isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <input
                type="email"
                placeholder="Email"
                value={authForm.email}
                onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                value={authForm.password}
                onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            {!isLogin && (
              <>
                <div>
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={authForm.full_name}
                    onChange={(e) => setAuthForm({...authForm, full_name: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <input
                    type="text"
                    placeholder="Country"
                    value={authForm.country}
                    onChange={(e) => setAuthForm({...authForm, country: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <input
                    type="tel"
                    placeholder="Phone (optional)"
                    value={authForm.phone}
                    onChange={(e) => setAuthForm({...authForm, phone: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50"
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Create Account')}
            </button>
          </form>
        </div>
      </div>
    );
  }

  const getNavItems = () => {
    const baseItems = ['dashboard'];
    
    if (user.role === 'member') {
      return [...baseItems, 'deposits', 'applications', 'repayments'];
    }
    
    if (isAdmin()) {
      return [...baseItems, 'deposits', 'applications', 'repayments', 'manage-users', 'manage-applications'];
    }
    
    return baseItems;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Fund Manager</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user.full_name}</span>
              {getRoleBadge(user.role)}
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <nav className="flex space-x-8 mb-8 overflow-x-auto">
          {getNavItems().map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === 'deposits') fetchDeposits();
                if (tab === 'applications') fetchApplications();
                if (tab === 'repayments') fetchRepayments();
                if (tab === 'manage-users' || tab === 'manage-applications') fetchAdminData();
              }}
              className={`px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.replace('-', ' ').charAt(0).toUpperCase() + tab.replace('-', ' ').slice(1)}
            </button>
          ))}
        </nav>

        {/* Content */}
        {activeTab === 'dashboard' && dashboard && (
          <div className="space-y-6">
            {/* Role-specific dashboard content */}
            {dashboard.role === 'member' && (
              <>
                {/* Member Dashboard */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-md">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Deposits</p>
                        <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.total_deposits)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-md">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Finance Applications</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.total_applications}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-red-100 rounded-md">
                        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Pending Repayments</p>
                        <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.pending_repayments)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {dashboard.role === 'country_coordinator' && (
              <>
                {/* Country Coordinator Dashboard */}
                <div className="bg-blue-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-blue-900 mb-2">Country Coordinator - {dashboard.country}</h2>
                  <p className="text-blue-700">Manage members and applications in your country</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-md">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Country Members</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.country_members}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-yellow-100 rounded-md">
                        <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Pending Applications</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.pending_applications}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-md">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Deposits</p>
                        <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.total_deposits_in_country)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {dashboard.role === 'fund_admin' && (
              <>
                {/* Fund Admin Dashboard */}
                <div className="bg-purple-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-purple-900 mb-2">Fund Administrator</h2>
                  <p className="text-purple-700">Manage fund disbursals and high-value applications</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-md">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Members</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.total_members}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-md">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Fund Value</p>
                        <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.total_fund_value)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-yellow-100 rounded-md">
                        <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Applications</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.total_applications}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-purple-100 rounded-md">
                        <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Disbursed Amount</p>
                        <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.disbursed_amount)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {dashboard.role === 'general_admin' && (
              <>
                {/* General Admin Dashboard */}
                <div className="bg-red-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-red-900 mb-2">System Administrator</h2>
                  <p className="text-red-700">Complete system oversight and user management</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-md">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Users</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.total_users}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-md">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Deposits</p>
                        <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.total_deposits)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Role Distribution</h3>
                    <div className="space-y-1">
                      {dashboard.role_distribution.map((role) => (
                        <div key={role._id} className="flex justify-between text-sm">
                          <span className="capitalize">{role._id.replace('_', ' ')}</span>
                          <span className="font-medium">{role.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Manage Users Tab (Admin Only) */}
        {activeTab === 'manage-users' && isAdmin() && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h3 className="text-lg font-medium text-gray-900">User Management</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Country</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    {isGeneralAdmin() && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {adminData.users.map((adminUser) => (
                    <tr key={adminUser.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{adminUser.full_name}</div>
                          <div className="text-sm text-gray-500">{adminUser.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {adminUser.country}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getRoleBadge(adminUser.role)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(adminUser.created_at)}
                      </td>
                      {isGeneralAdmin() && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <select
                            value={adminUser.role}
                            onChange={(e) => updateUserRole(adminUser.id, e.target.value)}
                            className="text-sm border border-gray-300 rounded px-2 py-1"
                          >
                            <option value="member">Member</option>
                            <option value="country_coordinator">Country Coordinator</option>
                            <option value="fund_admin">Fund Admin</option>
                            <option value="general_admin">General Admin</option>
                          </select>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Manage Applications Tab (Admin Only) */}
        {activeTab === 'manage-applications' && isAdmin() && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h3 className="text-lg font-medium text-gray-900">Application Management</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applicant</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purpose</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {adminData.allApplications.map((app) => (
                    <tr key={app.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        User ID: {app.user_id.substr(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(app.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {app.purpose}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(app.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex space-x-2">
                          {app.status === 'pending' && (
                            <>
                              <button
                                onClick={() => updateApplicationStatus(app.id, 'approved')}
                                className="text-green-600 hover:text-green-800 text-xs bg-green-100 px-2 py-1 rounded"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => updateApplicationStatus(app.id, 'rejected')}
                                className="text-red-600 hover:text-red-800 text-xs bg-red-100 px-2 py-1 rounded"
                              >
                                Reject
                              </button>
                            </>
                          )}
                          {app.status === 'approved' && isFundAdmin() && (
                            <button
                              onClick={() => updateApplicationStatus(app.id, 'disbursed')}
                              className="text-purple-600 hover:text-purple-800 text-xs bg-purple-100 px-2 py-1 rounded"
                            >
                              Disburse
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Regular user tabs (existing functionality) */}
        {activeTab === 'deposits' && (
          <div className="space-y-6">
            {/* Add Deposit Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Record New Deposit</h3>
              <form onSubmit={handleDeposit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="number"
                  step="0.01"
                  placeholder="Amount"
                  value={depositForm.amount}
                  onChange={(e) => setDepositForm({...depositForm, amount: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <input
                  type="text"
                  placeholder="Description (optional)"
                  value={depositForm.description}
                  onChange={(e) => setDepositForm({...depositForm, description: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add Deposit'}
                </button>
              </form>
            </div>

            {/* Deposits List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Your Deposits</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {deposits.map((deposit) => (
                      <tr key={deposit.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(deposit.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {deposit.description || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(deposit.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(deposit.status)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {deposits.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No deposits found. Record your first deposit above!
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="space-y-6">
            {/* Add Application Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Submit Finance Application</h3>
              <form onSubmit={handleApplication} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Requested Amount"
                    value={applicationForm.amount}
                    onChange={(e) => setApplicationForm({...applicationForm, amount: e.target.value})}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Duration (months)"
                    value={applicationForm.requested_duration_months}
                    onChange={(e) => setApplicationForm({...applicationForm, requested_duration_months: e.target.value})}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <input
                  type="text"
                  placeholder="Purpose"
                  value={applicationForm.purpose}
                  onChange={(e) => setApplicationForm({...applicationForm, purpose: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <textarea
                  placeholder="Additional Description (optional)"
                  value={applicationForm.description}
                  onChange={(e) => setApplicationForm({...applicationForm, description: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="3"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Submit Application'}
                </button>
              </form>
            </div>

            {/* Applications List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Your Applications</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purpose</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {applications.map((app) => (
                      <tr key={app.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(app.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {app.purpose}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {app.requested_duration_months} months
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(app.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(app.status)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {applications.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No applications found. Submit your first application above!
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'repayments' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h3 className="text-lg font-medium text-gray-900">Your Repayments</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Installment</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Paid Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {repayments.map((repayment) => (
                    <tr key={repayment.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(repayment.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        #{repayment.installment_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(repayment.due_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {repayment.paid_date ? formatDate(repayment.paid_date) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(repayment.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {repayments.length === 0 && (
                <div className="p-6 text-center text-gray-500">
                  No repayments found.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;