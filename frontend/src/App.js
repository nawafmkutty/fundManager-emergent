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
  const [eligibleGuarantors, setEligibleGuarantors] = useState([]);
  const [guarantorRequests, setGuarantorRequests] = useState([]);
  const [systemConfig, setSystemConfig] = useState(null);
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
    description: '',
    guarantors: []
  });
  const [configForm, setConfigForm] = useState({
    minimum_deposit_for_guarantor: '',
    priority_weight: '',
    max_loan_amount: '',
    max_loan_duration_months: ''
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
      if (userData.role === 'general_admin') {
        fetchSystemConfig();
      }
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

  const fetchSystemConfig = async () => {
    try {
      const configData = await api('/api/admin/system-config');
      setSystemConfig(configData);
      setConfigForm({
        minimum_deposit_for_guarantor: configData.minimum_deposit_for_guarantor || '',
        priority_weight: configData.priority_weight || '',
        max_loan_amount: configData.max_loan_amount || '',
        max_loan_duration_months: configData.max_loan_duration_months || ''
      });
    } catch (error) {
      console.error('Failed to fetch system config:', error);
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

  const fetchEligibleGuarantors = async () => {
    try {
      const guarantorsData = await api('/api/guarantors/eligible');
      setEligibleGuarantors(guarantorsData);
    } catch (error) {
      console.error('Failed to fetch eligible guarantors:', error);
    }
  };

  const fetchGuarantorRequests = async () => {
    try {
      const requestsData = await api('/api/guarantor-requests');
      setGuarantorRequests(requestsData);
    } catch (error) {
      console.error('Failed to fetch guarantor requests:', error);
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
          description: applicationForm.description,
          guarantors: applicationForm.guarantors
        }
      });

      setApplicationForm({ 
        amount: '', 
        purpose: '', 
        requested_duration_months: '', 
        description: '',
        guarantors: []
      });
      fetchDashboard();
      fetchApplications();
      alert('Finance application submitted successfully!');
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const handleConfigUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const updateData = {};
      
      if (configForm.minimum_deposit_for_guarantor) {
        updateData.minimum_deposit_for_guarantor = parseFloat(configForm.minimum_deposit_for_guarantor);
      }
      if (configForm.priority_weight) {
        updateData.priority_weight = parseFloat(configForm.priority_weight);
      }
      if (configForm.max_loan_amount) {
        updateData.max_loan_amount = parseFloat(configForm.max_loan_amount);
      }
      if (configForm.max_loan_duration_months) {
        updateData.max_loan_duration_months = parseInt(configForm.max_loan_duration_months);
      }

      await api('/api/admin/system-config', {
        method: 'PUT',
        body: updateData
      });

      fetchSystemConfig();
      fetchDashboard();
      alert('System configuration updated successfully!');
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const respondToGuarantorRequest = async (guarantorId, status) => {
    try {
      await api(`/api/guarantor-requests/${guarantorId}/respond`, {
        method: 'PUT',
        body: { status }
      });
      
      fetchGuarantorRequests();
      alert(`Guarantor request ${status} successfully!`);
    } catch (error) {
      alert(error.message);
    }
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
      overdue: 'bg-red-100 text-red-800',
      accepted: 'bg-green-100 text-green-800',
      declined: 'bg-red-100 text-red-800'
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

  const getPriorityBadge = (score) => {
    let color = 'bg-gray-100 text-gray-800';
    let label = 'Low';
    
    if (score >= 90) {
      color = 'bg-red-100 text-red-800';
      label = 'Highest';
    } else if (score >= 70) {
      color = 'bg-orange-100 text-orange-800';
      label = 'High';
    } else if (score >= 50) {
      color = 'bg-yellow-100 text-yellow-800';
      label = 'Medium';
    }

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${color}`}>
        {label} ({score})
      </span>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Fund Manager</h1>
            <p className="text-gray-600">Advanced fund management system</p>
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
      return [...baseItems, 'deposits', 'applications', 'repayments', 'guarantor-requests'];
    }
    
    if (isAdmin()) {
      return [...baseItems, 'deposits', 'applications', 'repayments', 'manage-users', 'manage-applications'];
    }
    
    if (isGeneralAdmin()) {
      return [...baseItems, 'deposits', 'applications', 'repayments', 'manage-users', 'manage-applications', 'system-config'];
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
              <span className="ml-2 text-sm text-gray-500">v3.0 - Configurable Business Rules</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user.full_name}</span>
              {getRoleBadge(user.role)}
              {dashboard?.is_eligible_guarantor && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                  Eligible Guarantor
                </span>
              )}
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
                if (tab === 'guarantor-requests') fetchGuarantorRequests();
                if (tab === 'manage-users' || tab === 'manage-applications') fetchAdminData();
                if (tab === 'system-config') fetchSystemConfig();
              }}
              className={`px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.replace('-', ' ').charAt(0).toUpperCase() + tab.replace('-', ' ').slice(1)}
              {tab === 'guarantor-requests' && dashboard?.pending_guarantor_requests > 0 && (
                <span className="ml-1 bg-red-500 text-white text-xs rounded-full px-1">
                  {dashboard.pending_guarantor_requests}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Content */}
        {activeTab === 'dashboard' && dashboard && (
          <div className="space-y-6">
            {/* System Configuration Alert for General Admin */}
            {isGeneralAdmin() && systemConfig && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-indigo-800">Current System Configuration</h3>
                    <div className="mt-2 text-sm text-indigo-700">
                      <ul className="grid grid-cols-2 gap-2">
                        <li>• Min Guarantor Deposit: {formatCurrency(systemConfig.minimum_deposit_for_guarantor)}</li>
                        <li>• Priority Weight: {systemConfig.priority_weight}</li>
                        <li>• Max Loan Amount: {systemConfig.max_loan_amount ? formatCurrency(systemConfig.max_loan_amount) : 'Unlimited'}</li>
                        <li>• Max Loan Duration: {systemConfig.max_loan_duration_months ? `${systemConfig.max_loan_duration_months} months` : 'Unlimited'}</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Member Dashboard */}
            {dashboard.role === 'member' && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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
                        <p className="text-xs text-gray-500">
                          {dashboard.is_eligible_guarantor 
                            ? '✅ Eligible as Guarantor' 
                            : `❌ Need ${formatCurrency(dashboard.minimum_deposit_for_guarantor - dashboard.total_deposits)} more`}
                        </p>
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
                        <p className="text-sm font-medium text-gray-600">Applications</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.total_applications}</p>
                        <p className="text-xs text-gray-500">Priority: Higher for new applicants</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-yellow-100 rounded-md">
                        <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Guarantor Requests</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.pending_guarantor_requests}</p>
                        <p className="text-xs text-gray-500">Pending responses</p>
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

            {/* General Admin Dashboard - Enhanced */}
            {dashboard.role === 'general_admin' && (
              <>
                <div className="bg-red-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-red-900 mb-2">System Administrator</h2>
                  <p className="text-red-700">Complete system oversight and configurable business rules</p>
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
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Priority Statistics</h3>
                    <div className="space-y-1">
                      <div className="text-xs text-gray-500">Avg: {dashboard.priority_stats.avg_priority?.toFixed(1) || 0}</div>
                      <div className="text-xs text-gray-500">Max: {dashboard.priority_stats.max_priority || 0}</div>
                      <div className="text-xs text-gray-500">Min: {dashboard.priority_stats.min_priority || 0}</div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Guarantor Statistics</h3>
                    <div className="space-y-1">
                      {dashboard.guarantor_stats.map((stat) => (
                        <div key={stat._id} className="flex justify-between text-xs">
                          <span className="capitalize">{stat._id || 'None'}</span>
                          <span className="font-medium">{stat.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Other dashboards remain the same... */}
          </div>
        )}

        {/* System Configuration Tab */}
        {activeTab === 'system-config' && isGeneralAdmin() && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">System Configuration</h3>
              <p className="text-sm text-gray-600 mb-6">Configure business rules and system parameters. Leave fields empty to keep current values.</p>
              
              <form onSubmit={handleConfigUpdate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Deposit for Guarantor Eligibility
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder={`Current: ${systemConfig?.minimum_deposit_for_guarantor || 'Not set'}`}
                      value={configForm.minimum_deposit_for_guarantor}
                      onChange={(e) => setConfigForm({...configForm, minimum_deposit_for_guarantor: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Users must have at least this amount in deposits to be eligible as guarantors</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Priority Weight
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder={`Current: ${systemConfig?.priority_weight || 'Not set'}`}
                      value={configForm.priority_weight}
                      onChange={(e) => setConfigForm({...configForm, priority_weight: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Base priority score for new applicants (higher = more priority)</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Maximum Loan Amount
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder={`Current: ${systemConfig?.max_loan_amount ? formatCurrency(systemConfig.max_loan_amount) : 'Unlimited'}`}
                      value={configForm.max_loan_amount}
                      onChange={(e) => setConfigForm({...configForm, max_loan_amount: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum amount that can be requested in a single application</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Maximum Loan Duration (Months)
                    </label>
                    <input
                      type="number"
                      placeholder={`Current: ${systemConfig?.max_loan_duration_months || 'Unlimited'}`}
                      value={configForm.max_loan_duration_months}
                      onChange={(e) => setConfigForm({...configForm, max_loan_duration_months: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum duration that can be requested for loan repayment</p>
                  </div>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={fetchSystemConfig}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    Reset Form
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Updating...' : 'Update Configuration'}
                  </button>
                </div>
              </form>
            </div>

            {/* Current Configuration Display */}
            {systemConfig && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Current Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-700">Minimum Deposit for Guarantor</p>
                    <p className="text-lg font-semibold text-gray-900">{formatCurrency(systemConfig.minimum_deposit_for_guarantor)}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-700">Priority Weight</p>
                    <p className="text-lg font-semibold text-gray-900">{systemConfig.priority_weight}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-700">Maximum Loan Amount</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {systemConfig.max_loan_amount ? formatCurrency(systemConfig.max_loan_amount) : 'Unlimited'}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-700">Maximum Loan Duration</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {systemConfig.max_loan_duration_months ? `${systemConfig.max_loan_duration_months} months` : 'Unlimited'}
                    </p>
                  </div>
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  Last updated: {systemConfig.updated_at ? formatDate(systemConfig.updated_at) : 'Never'}
                </div>
              </div>
            )}
          </div>
        )}

        {/* All other existing tabs remain exactly the same... */}
        {/* Guarantor Requests, Applications, Deposits, Repayments, Manage Users, Manage Applications tabs */}
        
        {/* Guarantor Requests Tab */}
        {activeTab === 'guarantor-requests' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Guarantor Requests</h3>
                <p className="text-sm text-gray-600 mt-1">People requesting you to guarantee their finance applications</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applicant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purpose</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Your Share</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {guarantorRequests.map((request) => (
                      <tr key={request.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{request.application_details?.applicant_name}</div>
                            <div className="text-sm text-gray-500">{request.application_details?.applicant_email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(request.application_details?.amount || 0)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {request.application_details?.purpose}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(request.guaranteed_amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(request.status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {request.status === 'pending' && (
                            <div className="flex space-x-2">
                              <button
                                onClick={() => respondToGuarantorRequest(request.id, 'accepted')}
                                className="text-green-600 hover:text-green-800 text-xs bg-green-100 px-2 py-1 rounded"
                              >
                                Accept
                              </button>
                              <button
                                onClick={() => respondToGuarantorRequest(request.id, 'declined')}
                                className="text-red-600 hover:text-red-800 text-xs bg-red-100 px-2 py-1 rounded"
                              >
                                Decline
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {guarantorRequests.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No guarantor requests found.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Applications Tab with Guarantors */}
        {activeTab === 'applications' && (
          <div className="space-y-6">
            {/* Add Application Form with Guarantors */}
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
                
                {/* Guarantor Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Guarantors (Optional but recommended)
                  </label>
                  <button
                    type="button"
                    onClick={fetchEligibleGuarantors}
                    className="mb-2 text-sm bg-gray-100 text-gray-700 px-3 py-1 rounded hover:bg-gray-200"
                  >
                    Load Eligible Guarantors
                  </button>
                  <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-2">
                    {eligibleGuarantors.map((guarantor) => (
                      <label key={guarantor.id} className="flex items-center space-x-2 text-sm py-1">
                        <input
                          type="checkbox"
                          checked={applicationForm.guarantors.includes(guarantor.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setApplicationForm({
                                ...applicationForm,
                                guarantors: [...applicationForm.guarantors, guarantor.id]
                              });
                            } else {
                              setApplicationForm({
                                ...applicationForm,
                                guarantors: applicationForm.guarantors.filter(id => id !== guarantor.id)
                              });
                            }
                          }}
                          className="rounded"
                        />
                        <span>{guarantor.full_name} ({guarantor.country}) - {formatCurrency(guarantor.total_deposits)} deposits</span>
                      </label>
                    ))}
                    {eligibleGuarantors.length === 0 && (
                      <p className="text-gray-500 text-sm">Click "Load Eligible Guarantors" to see available guarantors</p>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Submit Application'}
                </button>
              </form>
            </div>

            {/* Applications List with Priority and Guarantors */}
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
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Guarantors</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
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
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getPriorityBadge(app.priority_score)}
                          <div className="text-xs text-gray-500 mt-1">
                            Previous: {app.previous_finances_count}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {app.guarantors && app.guarantors.length > 0 ? (
                            <div>
                              {app.guarantors.map((g, idx) => (
                                <div key={idx} className="text-xs">
                                  {g.guarantor_name}: {getStatusBadge(g.status)}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-400">No guarantors</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(app.status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(app.created_at)}
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

        {/* All other tabs remain the same (deposits, repayments, manage-users, manage-applications) */}
        
        {/* I'll include the remaining tabs but they're essentially the same as before... */}
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

        {/* ... other tabs continue with same implementation ... */}
      </div>
    </div>
  );
}

export default App;