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
  const [approvalQueue, setApprovalQueue] = useState([]);
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
    max_loan_duration_months: '',
    country_coordinator_limit: '',
    fund_admin_limit: ''
  });
  const [approvalForm, setApprovalForm] = useState({
    action: 'approve',
    review_notes: '',
    conditions: '',
    recommended_amount: ''
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

  const fetchApprovalQueue = async () => {
    try {
      const queueData = await api('/api/admin/approval-queue');
      setApprovalQueue(queueData);
    } catch (error) {
      console.error('Failed to fetch approval queue:', error);
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
        max_loan_duration_months: configData.max_loan_duration_months || '',
        country_coordinator_limit: configData.country_coordinator_limit || '',
        fund_admin_limit: configData.fund_admin_limit || ''
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
      if (configForm.country_coordinator_limit) {
        updateData.country_coordinator_limit = parseFloat(configForm.country_coordinator_limit);
      }
      if (configForm.fund_admin_limit) {
        updateData.fund_admin_limit = parseFloat(configForm.fund_admin_limit);
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

  const handleApproval = async (applicationId, approvalData) => {
    try {
      setLoading(true);
      await api(`/api/admin/applications/${applicationId}/approve`, {
        method: 'PUT',
        body: approvalData
      });
      
      fetchApprovalQueue();
      fetchAdminData();
      fetchDashboard();
      alert('Application processed successfully!');
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

  const isAdmin = () => {
    return user && ['country_coordinator', 'fund_admin', 'general_admin'].includes(user.role);
  };

  const isGeneralAdmin = () => {
    return user && user.role === 'general_admin';
  };

  const isFundAdmin = () => {
    return user && ['fund_admin', 'general_admin'].includes(user.role);
  };

  const canApprove = () => {
    return user && ['country_coordinator', 'fund_admin', 'general_admin'].includes(user.role);
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
      requires_higher_approval: 'bg-orange-100 text-orange-800',
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

  const getApprovalLevelBadge = (level) => {
    if (!level) {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
          NOT SET
        </span>
      );
    }

    const colors = {
      country_coordinator: 'bg-blue-100 text-blue-800',
      fund_admin: 'bg-purple-100 text-purple-800',
      general_admin: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[level] || 'bg-gray-100 text-gray-800'}`}>
        {level.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Fund Manager</h1>
            <p className="text-gray-600">Advanced fund management with approval workflow</p>
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
      const adminItems = [...baseItems, 'deposits', 'applications', 'repayments', 'manage-users', 'manage-applications'];
      
      if (canApprove()) {
        adminItems.push('approval-queue');
      }
      
      if (isGeneralAdmin()) {
        adminItems.push('system-config');
      }
      
      return adminItems;
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
              <span className="ml-2 text-sm text-gray-500">v4.0 - Approval Workflow</span>
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
                if (tab === 'approval-queue') fetchApprovalQueue();
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
              {tab === 'approval-queue' && dashboard?.pending_approval > 0 && (
                <span className="ml-1 bg-orange-500 text-white text-xs rounded-full px-1">
                  {dashboard.pending_approval}
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
                    <h3 className="text-sm font-medium text-indigo-800">Approval Limits Configuration</h3>
                    <div className="mt-2 text-sm text-indigo-700">
                      <ul className="grid grid-cols-2 gap-2">
                        <li>• Country Coordinators: {formatCurrency(systemConfig.country_coordinator_limit)}</li>
                        <li>• Fund Admins: {formatCurrency(systemConfig.fund_admin_limit)}</li>
                        <li>• Min Guarantor Deposit: {formatCurrency(systemConfig.minimum_deposit_for_guarantor)}</li>
                        <li>• Priority Weight: {systemConfig.priority_weight}</li>
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
                        <div className="text-xs text-gray-500">
                          <span className="text-orange-600">Pending: {dashboard.pending_applications}</span> | 
                          <span className="text-green-600 ml-1">Approved: {dashboard.approved_applications}</span>
                        </div>
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

            {/* Country Coordinator Dashboard */}
            {dashboard.role === 'country_coordinator' && (
              <>
                <div className="bg-blue-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-blue-900 mb-2">Country Coordinator - {dashboard.country}</h2>
                  <p className="text-blue-700">Approval limit: {formatCurrency(dashboard.approval_limit)}</p>
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
                        <p className="text-sm font-medium text-gray-600">Country Members</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.country_members}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-orange-100 rounded-md">
                        <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Pending Approval</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.pending_approval}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-red-100 rounded-md">
                        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Needs Escalation</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.needs_escalation}</p>
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

            {/* Fund Admin Dashboard */}
            {dashboard.role === 'fund_admin' && (
              <>
                <div className="bg-purple-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-purple-900 mb-2">Fund Administrator</h2>
                  <p className="text-purple-700">Approval limit: {formatCurrency(dashboard.approval_limit)}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-orange-100 rounded-md">
                        <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Pending Approval</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.pending_approval}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-yellow-100 rounded-md">
                        <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">High Value Applications</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.high_value_applications}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-md">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Ready for Disbursement</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.ready_for_disbursement}</p>
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

            {/* General Admin Dashboard */}
            {dashboard.role === 'general_admin' && (
              <>
                <div className="bg-red-50 rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-red-900 mb-2">System Administrator</h2>
                  <p className="text-red-700">Complete system oversight with unlimited approval authority</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-red-100 rounded-md">
                        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">High Value Approvals</p>
                        <p className="text-2xl font-semibold text-gray-900">{dashboard.pending_high_value}</p>
                      </div>
                    </div>
                  </div>

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
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Approval Statistics</h3>
                    <div className="space-y-1">
                      {dashboard.approval_stats.map((stat) => (
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
          </div>
        )}

        {/* Approval Queue Tab */}
        {activeTab === 'approval-queue' && canApprove() && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Approval Queue</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Applications requiring your approval (sorted by priority)
                  {dashboard?.approval_limit && (
                    <span className="ml-2 font-medium">Your approval limit: {formatCurrency(dashboard.approval_limit)}</span>
                  )}
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applicant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Required Level</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {approvalQueue.map((app) => (
                      <tr key={app.id} className={!app.can_approve ? 'bg-gray-50' : ''}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{app.applicant_name}</div>
                            <div className="text-sm text-gray-500">{app.applicant_country}</div>
                            <div className="text-xs text-gray-400">{app.purpose}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{formatCurrency(app.amount)}</div>
                          <div className="text-xs text-gray-500">{app.requested_duration_months} months</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getPriorityBadge(app.priority_score)}
                          <div className="text-xs text-gray-500 mt-1">
                            Previous: {app.previous_finances_count}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getApprovalLevelBadge(app.required_approval_level)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(app.status)}
                          {app.approval_history && app.approval_history.length > 0 && (
                            <div className="text-xs text-gray-500 mt-1">
                              Last: {app.approval_history[app.approval_history.length - 1].action} by {app.approval_history[app.approval_history.length - 1].approver_name}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {app.can_approve ? (
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleApproval(app.id, { action: 'approve', review_notes: 'Approved via quick action' })}
                                className="text-green-600 hover:text-green-800 text-xs bg-green-100 px-2 py-1 rounded"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleApproval(app.id, { action: 'reject', review_notes: 'Rejected via quick action' })}
                                className="text-red-600 hover:text-red-800 text-xs bg-red-100 px-2 py-1 rounded"
                              >
                                Reject
                              </button>
                              <button
                                onClick={() => {
                                  const notes = prompt('Enter review notes:');
                                  if (notes) {
                                    handleApproval(app.id, { action: 'request_more_info', review_notes: notes });
                                  }
                                }}
                                className="text-blue-600 hover:text-blue-800 text-xs bg-blue-100 px-2 py-1 rounded"
                              >
                                More Info
                              </button>
                              {user.role !== 'general_admin' && (
                                <button
                                  onClick={() => handleApproval(app.id, { action: 'escalate', review_notes: 'Escalated to higher authority' })}
                                  className="text-orange-600 hover:text-orange-800 text-xs bg-orange-100 px-2 py-1 rounded"
                                >
                                  Escalate
                                </button>
                              )}
                            </div>
                          ) : (
                            <div className="text-xs text-red-600">
                              {app.approval_restriction}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {approvalQueue.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No applications pending your approval.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* System Configuration Tab */}
        {activeTab === 'system-config' && isGeneralAdmin() && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">System Configuration</h3>
              <p className="text-sm text-gray-600 mb-6">Configure business rules, approval limits, and system parameters.</p>
              
              <form onSubmit={handleConfigUpdate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Country Coordinator Approval Limit
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder={`Current: ${systemConfig?.country_coordinator_limit || 'Not set'}`}
                      value={configForm.country_coordinator_limit}
                      onChange={(e) => setConfigForm({...configForm, country_coordinator_limit: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum amount country coordinators can approve</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Fund Admin Approval Limit
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder={`Current: ${systemConfig?.fund_admin_limit || 'Not set'}`}
                      value={configForm.fund_admin_limit}
                      onChange={(e) => setConfigForm({...configForm, fund_admin_limit: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Maximum amount fund admins can approve</p>
                  </div>

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
                    <p className="text-xs text-gray-500 mt-1">Base priority score for new applicants</p>
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
                <h3 className="text-lg font-medium text-gray-900 mb-4">Current Approval Workflow Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-blue-700">Country Coordinator Limit</p>
                    <p className="text-lg font-semibold text-blue-900">{formatCurrency(systemConfig.country_coordinator_limit)}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-purple-700">Fund Admin Limit</p>
                    <p className="text-lg font-semibold text-purple-900">{formatCurrency(systemConfig.fund_admin_limit)}</p>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-red-700">General Admin Limit</p>
                    <p className="text-lg font-semibold text-red-900">Unlimited</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-green-700">Guarantor Min Deposit</p>
                    <p className="text-lg font-semibold text-green-900">{formatCurrency(systemConfig.minimum_deposit_for_guarantor)}</p>
                  </div>
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-yellow-700">Priority Weight</p>
                    <p className="text-lg font-semibold text-yellow-900">{systemConfig.priority_weight}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-700">Max Loan Amount</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {systemConfig.max_loan_amount ? formatCurrency(systemConfig.max_loan_amount) : 'Unlimited'}
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

        {/* All other existing tabs remain the same... */}
        {/* (keeping the existing deposits, applications, guarantor-requests, manage-users, manage-applications tabs) */}
        
        {/* Enhanced Applications Tab with Approval History */}
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

            {/* Applications List with Priority, Guarantors, and Approval History */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Your Applications</h3>
              </div>
              <div className="space-y-4 p-6">
                {applications.map((app) => (
                  <div key={app.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-lg font-medium text-gray-900">{formatCurrency(app.amount)}</h4>
                          {getPriorityBadge(app.priority_score)}
                          {getStatusBadge(app.status)}
                        </div>
                        <p className="text-sm text-gray-600">{app.purpose}</p>
                        <p className="text-xs text-gray-500">
                          Duration: {app.requested_duration_months} months | 
                          Previous finances: {app.previous_finances_count} |
                          Applied: {formatDate(app.created_at)}
                        </p>
                      </div>
                    </div>

                    {/* Guarantors */}
                    {app.guarantors && app.guarantors.length > 0 && (
                      <div className="mb-3">
                        <h5 className="text-sm font-medium text-gray-700 mb-1">Guarantors</h5>
                        <div className="flex flex-wrap gap-2">
                          {app.guarantors.map((g, idx) => (
                            <div key={idx} className="text-xs bg-gray-100 px-2 py-1 rounded">
                              {g.guarantor_name}: {getStatusBadge(g.status)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Approval History */}
                    {app.approval_history && app.approval_history.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 mb-2">Approval History</h5>
                        <div className="space-y-2">
                          {app.approval_history.map((history, idx) => (
                            <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                              <div className="flex justify-between items-start">
                                <span className="font-medium">{history.approver_name} ({history.approver_role.replace('_', ' ')})</span>
                                <span className="text-gray-500">{formatDate(history.created_at)}</span>
                              </div>
                              <div className="mt-1">
                                <span className={`px-2 py-1 rounded text-xs ${
                                  history.action === 'approve' ? 'bg-green-100 text-green-800' :
                                  history.action === 'reject' ? 'bg-red-100 text-red-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {history.action.toUpperCase()}
                                </span>
                                {history.review_notes && (
                                  <span className="ml-2 text-gray-600">"{history.review_notes}"</span>
                                )}
                              </div>
                              {history.conditions && (
                                <div className="mt-1 text-gray-600">Conditions: {history.conditions}</div>
                              )}
                              {history.recommended_amount && (
                                <div className="mt-1 text-gray-600">Recommended amount: {formatCurrency(history.recommended_amount)}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {applications.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No applications found. Submit your first application above!
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Other existing tabs continue... */}
      </div>
    </div>
  );
}

export default App;